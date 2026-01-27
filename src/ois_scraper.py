"""
OIS Scraper using Playwright for proper CAPTCHA handling.
"""
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import re

from .config import Config
from .captcha_solver import solve_captcha


class OISScraper:
    """Scraper for OIS student portal using Playwright."""
    
    def __init__(self):
        self.browser: Browser | None = None
        self.logged_in = False
    
    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
    
    async def login(self, max_attempts: int = 10) -> bool:
        """
        Login to OIS portal using Playwright.
        
        Args:
            max_attempts: Maximum CAPTCHA solving attempts
            
        Returns:
            True if login successful, False otherwise
        """
        await self._ensure_browser()
        
        for attempt in range(max_attempts):
            context = await self.browser.new_context(device_scale_factor=2)
            page = await context.new_page()
            
            try:
                # Go to login page
                await page.goto(Config.OIS_LOGIN_URL, wait_until="networkidle")
                
                # Get CAPTCHA image with high quality screenshot (uses device_scale_factor=2)
                captcha_img = page.locator("#img_captcha")
                captcha_bytes = await captcha_img.screenshot(type="png", scale="device")
                
                # Solve the CAPTCHA
                captcha_text = solve_captcha(captcha_bytes)
                
                if not captcha_text:
                    await context.close()
                    continue
                
                # Fill in the form
                await page.fill("#kullanici_adi", Config.OIS_USERNAME)
                await page.fill("#kullanici_sifre", Config.OIS_PASSWORD)
                await page.fill("#captcha", captcha_text)
                
                # Submit the form
                await page.click('button[type="submit"]')
                
                # Wait for navigation
                await page.wait_for_load_state("networkidle")
                
                # Check if login was successful
                current_url = page.url
                if "/auth/login" not in current_url:
                    self.logged_in = True
                    self._context = context
                    self._page = page
                    return True
                
                # Check for error message - CAPTCHA wrong, try again
                content = await page.content()
                if "hatalı" in content.lower() or "yanlış" in content.lower():
                    print(f"[CAPTCHA] Attempt {attempt + 1}/{max_attempts} failed - retrying...")
                    await context.close()
                    continue  # Try again with new CAPTCHA
                    
            except Exception as e:
                print(f"Login attempt {attempt + 1} failed: {e}")
            
            await context.close()
        
        return False
    
    async def fetch_grades(self) -> Optional[dict]:
        """
        Fetch current grades from OIS.
        
        Returns:
            Dictionary of courses and their grades, or None if failed
        """
        if not self.logged_in:
            if not await self.login():
                return None
        
        try:
            await self._page.goto(Config.OIS_GRADES_URL, wait_until="networkidle")
            
            # Wait for table
            await self._page.wait_for_selector("table.a4")
            
            # DEBUG: Save HTML to inspect structure
            self._page_content = await self._page.content()
            # with open("data/debug_grades.html", "w", encoding="utf-8") as f:
            #     f.write(self._page_content)
            # print("[DEBUG] Saved grades page to data/debug_grades.html")
            
            # Parsing
            grades = self.parse_grades()
            print(f"[DEBUG] Parsed {len(grades)} courses")
            return grades
            
        except Exception as e:
            print(f"Failed to fetch grades: {e}")
            if self._page:
                try:
                    await self._page.screenshot(path="data/error_screenshot.png")
                    content = await self._page.content()
                    with open("data/error_page.html", "w", encoding="utf-8") as f:
                        f.write(content)
                    print("[DEBUG] Saved error info to data/error_screenshot.png and data/error_page.html")
                except:
                    pass
            self.logged_in = False
            return None
    
    def parse_grades(self) -> dict:
        """Parse grades from the current page."""
        soup = BeautifulSoup(self._page_content or "", "html.parser")
        
        # Find the main table
        # Based on HTML dump, tables have class 'a4'
        tables = soup.find_all("table", class_="a4")
        print(f"[DEBUG] Found {len(tables)} tables")
        
        grades = {}
        current_course = None
        
        for table in tables:
            rows = table.find_all("tr")
            print(f"[DEBUG] Table has {len(rows)} rows")
            
            for row in rows:
                # Look for course headers
                headers = row.find_all("th", class_="belge_satir")
                
                for header in headers:
                    # Fallback strategies for text extraction
                    full_text = header.get_text(" | ", strip=True)
                    print(f"[DEBUG] Header text: '{full_text}'")
                    
                    # Match course pattern: "1410211007 - Ders Adı"
                    # Try to match start of string
                    course_match = re.search(r'(\d{10})\s*-\s*(.+?)(?:\s*\||$)', full_text)

                    if course_match:
                        course_code = course_match.group(1)
                        # Clean up name by removing potential grade suffixes if regex didn't catch them
                        raw_name = course_match.group(2).strip()
                        # Split by " | " if present (separator we added)
                        course_name = raw_name.split(" | ")[0]
                        
                        print(f"[DEBUG] Found Course: {course_code} - {course_name}")
                        
                        # Extract letter grade and score from h3 tags
                        h3_tags = header.find_all("h3")
                        letter_grade = None
                        success_score = None
                        
                        for h3 in h3_tags:
                            h3_text = h3.get_text(strip=True)
                            if re.match(r'^[A-F][+-]?$', h3_text):
                                letter_grade = h3_text
                            score_match = re.search(r'Başarı Puanı:\s*([\d.]+)', h3_text)
                            if score_match:
                                success_score = float(score_match.group(1))
                        
                        current_course = {
                            "code": course_code,
                            "name": course_name,
                            "letter_grade": letter_grade,
                            "success_score": success_score,
                            "components": []
                        }
                        grades[course_code] = current_course
                
                # Look for grade components
                cells = row.find_all("td", class_="belge_satir")
                
                if len(cells) >= 3 and current_course:
                    weight_text = cells[0].get_text(strip=True)
                    component_name = cells[1].get_text(strip=True)
                    score_text = cells[2].get_text(strip=True)
                    
                    # Extract weight
                    weight_match = re.search(r'\(%(\d+)\)', weight_text)
                    weight = int(weight_match.group(1)) if weight_match else None
                    
                    # Extract score
                    try:
                        score = float(score_text)
                    except ValueError:
                        score = None
                    
                    # Extract date
                    date = None
                    if len(cells) >= 4:
                        date = cells[3].get_text(strip=True)
                    
                    if component_name and score is not None:
                        # Handle duplicate component names (e.g. multiple "Ara Sınavlar")
                        base_name = component_name
                        counter = 1
                        
                        # Check if name already exists in current components
                        existing_names = [c["name"] for c in current_course["components"]]
                        while component_name in existing_names:
                            counter += 1
                            component_name = f"{base_name} {counter}"
                        
                        current_course["components"].append({
                            "name": component_name,
                            "weight": weight,
                            "score": score,
                            "date": date
                        })
        
        return grades
    
    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        self.logged_in = False
