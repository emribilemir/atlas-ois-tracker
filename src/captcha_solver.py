import cv2
import numpy as np
import pytesseract
import io
import os


def get_tesseract_path() -> str | None:
    """Find Tesseract executable path."""
    env_path = os.getenv("TESSERACT_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    
    for path in windows_paths:
        if os.path.exists(path):
            return path
    
    return None


tesseract_path = get_tesseract_path()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


def solve_captcha(image_bytes: bytes, debug: bool = True) -> str:
    """
    Solve CAPTCHA using OpenCV preprocessing and Tesseract OCR.
    
    Args:
        image_bytes: Raw image bytes
        debug: Whether to save debug images
        
    Returns:
        Recognized text or empty string
    """
    debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(debug_dir, exist_ok=True)

    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return ""

        # 1. Convert to Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Thresholding
        # Invert binary threshold to make text white on black (better for morphology)
        _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)

        # 3. Morphological Operations (Noise Removal)
        # Kernel size is critical - 2x2 is good for thin lines
        kernel = np.ones((2,2), np.uint8)
        
        # Opening (Erosion followed by Dilation) removes noise
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Dilation thickens the text slightly
        dilated = cv2.dilate(opened, kernel, iterations=1)

        # 4. Invert back (Black text on white background)
        final_img = cv2.bitwise_not(dilated)

        # 5. Upscale
        # Scaling helps small text
        scale_percent = 300
        width = int(final_img.shape[1] * scale_percent / 100)
        height = int(final_img.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized = cv2.resize(final_img, dim, interpolation=cv2.INTER_CUBIC)

        if debug:
            cv2.imwrite(os.path.join(debug_dir, "captcha_original.png"), img)
            cv2.imwrite(os.path.join(debug_dir, "captcha_processed.png"), resized)
            print(f"[CAPTCHA] Debug images saved to {debug_dir}")

        # OCR Configuration
        # --psm 8: Treat the image as a single word
        # whitelist: Allow uppercase, lowercase, numbers
        custom_config = r'--psm 8 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        text = pytesseract.image_to_string(resized, config=custom_config)
        text = text.strip()
        text = ''.join(c for c in text if c.isalnum())

        if debug:
            print(f"[CAPTCHA] OCR result: '{text}'")

        # User request: Ignore result if not 4 characters
        if len(text) != 4:
            if debug:
                print(f"[CAPTCHA] Result length {len(text)} != 4, ignoring.")
            return ""

        return text

    except Exception as e:
        print(f"Error solving CAPTCHA: {e}")
        return ""
