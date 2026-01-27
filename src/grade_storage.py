"""
Grade storage - saves grades to JSON and detects changes.
"""
import json
import os
from typing import Optional
from .config import Config


class GradeStorage:
    """Handles storing and comparing grades."""
    
    def __init__(self):
        self.grades_file = Config.GRADES_FILE
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create grades file if it doesn't exist."""
        if not os.path.exists(self.grades_file):
            self.save({})
    
    def load(self) -> dict:
        """Load grades from file."""
        try:
            with open(self.grades_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def save(self, grades: dict):
        """Save grades to file."""
        with open(self.grades_file, "w", encoding="utf-8") as f:
            json.dump(grades, f, ensure_ascii=False, indent=2)
    
    def compare_and_update(self, new_grades: dict) -> list[dict]:
        """
        Compare new grades with stored grades and update.
        
        Args:
            new_grades: New grades dictionary
            
        Returns:
            List of changes detected
        """
        old_grades = self.load()
        changes = []
        
        for course_code, course_data in new_grades.items():
            old_course = old_grades.get(course_code, {})
            
            # Check for new letter grade
            new_letter = course_data.get("letter_grade")
            old_letter = old_course.get("letter_grade")
            
            if new_letter and new_letter != old_letter:
                changes.append({
                    "type": "letter_grade",
                    "course_code": course_code,
                    "course_name": course_data.get("name", ""),
                    "old_value": old_letter,
                    "new_value": new_letter,
                    "success_score": course_data.get("success_score")
                })
            
            # Check for new/changed component scores
            new_components = course_data.get("components", [])
            old_components = old_course.get("components", [])
            
            # Create a key for each component for comparison
            old_component_map = {
                (c.get("name"), c.get("weight")): c 
                for c in old_components
            }
            
            for component in new_components:
                key = (component.get("name"), component.get("weight"))
                old_component = old_component_map.get(key)
                
                if old_component is None:
                    # New component
                    changes.append({
                        "type": "new_score",
                        "course_code": course_code,
                        "course_name": course_data.get("name", ""),
                        "component": component.get("name"),
                        "weight": component.get("weight"),
                        "score": component.get("score"),
                        "date": component.get("date")
                    })
                elif component.get("score") != old_component.get("score"):
                    # Score changed
                    changes.append({
                        "type": "score_change",
                        "course_code": course_code,
                        "course_name": course_data.get("name", ""),
                        "component": component.get("name"),
                        "weight": component.get("weight"),
                        "old_score": old_component.get("score"),
                        "new_score": component.get("score"),
                        "date": component.get("date")
                    })
        
        # Save new grades
        self.save(new_grades)
        
        return changes
    
    def get_summary(self) -> str:
        """Get a summary of current grades."""
        grades = self.load()
        
        if not grades:
            return "📭 Henüz kaydedilmiş not yok."
        
        lines = ["📊 **Mevcut Notlar**\n"]
        
        for course_code, course_data in grades.items():
            name = course_data.get("name", course_code)
            letter = course_data.get("letter_grade", "—")
            score = course_data.get("success_score", "—")
            
            lines.append(f"• **{name}**: {letter} ({score})")
        
        return "\n".join(lines)


def format_changes(changes: list[dict]) -> str:
    """Format changes for Telegram notification - grouped by course."""
    if not changes:
        return ""
    
    # Group changes by course
    courses = {}
    for change in changes:
        code = change.get("course_code", "unknown")
        if code not in courses:
            courses[code] = {
                "name": change.get("course_name", ""),
                "letter_grade": None,
                "success_score": None,
                "components": []
            }
        
        if change["type"] == "letter_grade":
            courses[code]["letter_grade"] = {
                "old": change.get("old_value") or "—",
                "new": change.get("new_value")
            }
            courses[code]["success_score"] = change.get("success_score")
        
        elif change["type"] == "new_score":
            courses[code]["components"].append({
                "action": "new",
                "name": change.get("component"),
                "weight": change.get("weight"),
                "score": change.get("score")
            })
        
        elif change["type"] == "score_change":
            courses[code]["components"].append({
                "action": "change",
                "name": change.get("component"),
                "weight": change.get("weight"),
                "old": change.get("old_score"),
                "new": change.get("new_score")
            })
    
    # Format output
    lines = ["🔔 *Not Değişikliği!*\n"]
    
    for code, data in courses.items():
        name = data["name"] or code
        
        # Course header with grade if available
        if data["letter_grade"]:
            grade = data["letter_grade"]["new"]
            score = data["success_score"] or ""
            lines.append(f"📚 *{name}*")
            lines.append(f"   Not: {data['letter_grade']['old']} → *{grade}* ({score})")
        else:
            lines.append(f"📚 *{name}*")
        
        # Components
        for comp in data["components"]:
            weight = f"%{comp['weight']}" if comp.get('weight') else ""
            if comp["action"] == "new":
                lines.append(f"   • {comp['name']} {weight}: *{comp['score']}*")
            else:
                lines.append(f"   • {comp['name']}: {comp['old']} → *{comp['new']}*")
        
        lines.append("")  # Empty line between courses
    
    return "\n".join(lines).strip()


def format_full_grades(grades: dict) -> str:
    """Format full grade list for Telegram."""
    if not grades:
        return "📭 Henüz kayıtlı not yok."
    
    lines = ["📊 *Güncel Not Durumu*\n"]
    
    for code, data in grades.items():
        name = data.get("name", code)
        letter = data.get("letter_grade", "—")
        score = data.get("success_score", "—")
        
        lines.append(f"📚 *{name}*")
        
        # Main grade info
        if letter != "—" or score != "—":
            lines.append(f"   Not: *{letter}* ({score})")
        
        # Components
        components = data.get("components", [])
        if components:
            # Sort components by date if available, else by name
            # components.sort(key=lambda x: x.get("date") or "", reverse=True)
            
            for comp in components:
                c_name = comp.get("name", "Sınav")
                weight = f"%{comp.get('weight')}" if comp.get("weight") else ""
                val = comp.get("score", "—")
                
                # Format: • Ara Sınavlar %30: 86.0
                lines.append(f"   • {c_name} {weight}: *{val}*")
        
        lines.append("")  # Empty line between courses
    
    return "\n".join(lines).strip()

