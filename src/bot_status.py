from datetime import datetime

class BotStatus:
    """Shared state for bot status monitoring."""
    last_check_time: str = "Henüz kontrol yapılmadı"
    last_status: str = "Başlatılıyor..."
    last_grade_count: int = 0
    start_time: str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    check_count: int = 0
    exam_count: int = 0
