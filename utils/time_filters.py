from datetime import datetime, timedelta

def ago(value, short=False):
    """Format a datetime as a pretty 'time ago' string.
    
    Args:
        value (datetime): The datetime to format
        short (bool): Whether to use short format
        
    Returns:
        str: A human-readable string representing time elapsed
    """
    if not value:
        return ""
    
    now = datetime.utcnow()
    diff = now - value
    
    if diff < timedelta(seconds=10):
        return "just now"
    
    if diff < timedelta(minutes=1):
        seconds = diff.seconds
        return f"{seconds}s ago" if short else f"{seconds} second{'s' if seconds != 1 else ''} ago"
    
    if diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"{minutes}m ago" if short else f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    
    if diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f"{hours}h ago" if short else f"{hours} hour{'s' if hours != 1 else ''} ago"
    
    if diff < timedelta(days=7):
        days = diff.days
        return f"{days}d ago" if short else f"{days} day{'s' if days != 1 else ''} ago"
    
    if diff < timedelta(days=31):
        weeks = diff.days // 7
        return f"{weeks}w ago" if short else f"{weeks} week{'s' if weeks != 1 else ''} ago"
    
    if diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months}mo ago" if short else f"{months} month{'s' if months != 1 else ''} ago"
    
    years = diff.days // 365
    return f"{years}y ago" if short else f"{years} year{'s' if years != 1 else ''} ago"