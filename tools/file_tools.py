from langchain_core.tools import tool
import pytesseract
from PIL import Image


@tool
def read_file(filepath: str) -> str:
    """
    Read file from the specified path and return its content as a string.

    Args:
        filepath: The path to the file to read.

    Returns:
        The content of the file as a string, or an error message if reading fails.
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File not found at {filepath}"
    except Exception as e:
        return f"Error reading file {filepath}: {str(e)}"


@tool
def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using pytesseract (if available).

    Args:
        image_path: Path to the image file

    Returns:
        Extracted text as string or error message
    """
    try:

        # Open the image
        image = Image.open(image_path)

        # Extract text
        text = pytesseract.image_to_string(image)

        return f"Extracted text from image:\n\n{text}. You can use this to process answer."
    except ImportError:
        return "Error: pytesseract is not installed. Please install it with 'pip install pytesseract' and ensure Tesseract OCR is installed on your system."
    except Exception as e:
        return f"Error extracting text from image: {str(e)}"

@tool
def read_csv_file(file_path: str) -> str:
    """
    Extract data from a CSV file using pandas.

    Args:
        file_path: Path to the CSV file

    Returns:
        Data description as string or error message
    """
    try:
        import pandas as pd

        # Read the CSV file
        df = pd.read_csv(file_path)

        # Run various analyses based on the query
        result = f"CSV file loaded with {len(df)} rows and {len(df.columns)} columns.\n"
        result += f"Columns: {', '.join(df.columns)}\n\n"

        # Add summary statistics
        result += "Summary statistics:\n"
        result += str(df.describe())

        return f"Extracted data from table:\n\n{result}. You can use this to process answer."
    except ImportError:
        return "Error: pandas is not installed. Please install it with 'pip install pandas'."
    except Exception as e:
        return f"Error analyzing CSV file: {str(e)}"


@tool
def read_excel_file(file_path: str) -> str:
    """
    Extract data from an Excel file using pandas.

    Args:
        file_path: Path to the Excel file

    Returns:
        Data description as string or error message
    """
    try:
        import pandas as pd

        # Read the Excel file
        df = pd.read_excel(file_path)

        # Run various analyses based on the query
        result = f"Excel file loaded with {len(df)} rows and {len(df.columns)} columns.\n"
        result += f"Columns: {', '.join(df.columns)}\n\n"

        # Add summary statistics
        result += "Summary statistics:\n"
        result += str(df.describe())

        return f"Extracted data from table:\n\n{result}. You can use this to process answer."
    except ImportError:
        return "Error: pandas and openpyxl are not installed. Please install them with 'pip install pandas openpyxl'."
    except Exception as e:
        return f"Error analyzing Excel file: {str(e)}"