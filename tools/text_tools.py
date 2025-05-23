# from smolagents import tool
from langchain_core.tools import tool
import pandas as pd
from tabulate import tabulate
import re

@tool
def clean_text(text: str) -> str:
    """
    Clean and normalize text for better processing.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep punctuation
    text = ''.join(c for c in text if c.isalnum() or c.isspace() or c in '.,!?;:')
    
    return text.strip()

@tool
def format_dataframe(df: pd.DataFrame, format_type: str = "table") -> str:
    """
    Format a pandas DataFrame in a human-readable way.
    
    Args:
        df: DataFrame to format
        format_type: Type of formatting ("table", "markdown", "csv")
        
    Returns:
        Formatted string representation of the DataFrame
    """
    if format_type == "table":
        return tabulate(df, headers='keys', tablefmt='psql')
    elif format_type == "markdown":
        return df.to_markdown()
    elif format_type == "csv":
        return df.to_csv(index=False)
    else:
        return str(df)

@tool
def is_reversed_text(text: str) -> bool:
    """
    Check if the text appears to be reversed.
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be reversed, False otherwise
    """
    # Check if text contains reversed words or phrases
    reversed_patterns = [
        r'\b\w{3,}\b',  # Words with 3 or more letters
        r'\b[A-Z][a-z]+\b',  # Proper nouns
        r'\b\d{4}\b',  # Years
    ]
    
    for pattern in reversed_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # If the reversed version of the word is more common than the original,
            # it's likely reversed text
            if match[::-1] in text and match not in text:
                return True
    return False

@tool
def fix_reversed_text(text: str) -> str:
    """
    Fix reversed text by reversing it back to normal.
    
    Args:
        text: Potentially reversed text
        
    Returns:
        Fixed text
    """
    if is_reversed_text(text):
        return text[::-1]
    return text 