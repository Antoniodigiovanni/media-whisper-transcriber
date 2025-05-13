import re

def get_safe_file_name(title):
    """
    Given a string (the podcast or YT video title),
    get a string that can be safely used as file name.
    """
    # Replace invalid characters with underscores
    safe_title = re.sub(r'[^\w\-_.]', '_', title).lower()
        
    return safe_title