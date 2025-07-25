# skills/system.py
import datetime
from .skill_loader import aist_skill

@aist_skill
def get_current_time(timezone: str = "local") -> str:
    """
    Retrieves the current time.
    
    Args:
        timezone (str): The timezone to get the time for (currently only 'local' is supported).
        
    Returns:
        str: A string describing the current time.
    """
    now = datetime.datetime.now()
    return f"The current time is {now.strftime('%I:%M %p')}."

@aist_skill
def get_current_date() -> str:
    """
    Retrieves today's date.
    """
    today = datetime.date.today()
    return f"Today's date is {today.strftime('%B %d, %Y')}."