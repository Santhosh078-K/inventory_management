import os
import streamlit as st # Only used for st.warning now
from dotenv import load_dotenv # Import load_dotenv
from PIL import Image # For placeholder image generation

# Load environment variables from .env file at the start
load_dotenv()

# Predefined list of categories for consistency
ITEM_CATEGORIES = ["Electronics", "Books", "Clothing", "Home Goods", "Food", "Office Supplies", "Hardware", "Medical", "Automotive", "Other"]

# --- Base Directory Retrieval ---
# Define BASE_DIR as a module-level variable that is guaranteed to be a string.
# It prioritizes the script's directory but falls back to the current working directory.
def _get_base_dir_robust():
    """
    Robustly determines the base directory of the application.
    Always returns a string path, falling back to os.getcwd() if necessary.
    """
    try:
        # os.path.abspath(__file__) gives the full path to the current script (utils.py)
        current_file_path = os.path.abspath(__file__)
        # os.path.dirname gets the directory of that script
        if current_file_path and os.path.exists(current_file_path):
            return os.path.dirname(current_file_path)
        else:
            # Fallback if __file__ is not useful (e.g., in some interactive environments)
            return os.getcwd()
    except Exception as e:
        # Fallback to current working directory and print an error for debugging.
        print(f"Error determining script path: {e}. Falling back to os.getcwd().")
        return os.getcwd()

BASE_DIR = _get_base_dir_robust()


def get_pdf_dir():
    """Returns the path to the directory where PDFs are stored."""
    # Assuming utils.py is in the root of the project or a direct subdirectory
    # Adjust '..' if your utils.py is nested deeper (e.g., '../../static/pdfs')
    pdf_dir = os.path.join(BASE_DIR, 'static', 'pdfs')
    return pdf_dir

def get_image_dir():
    """Returns the path to the directory where images are stored."""
    images_dir = os.path.join(BASE_DIR, 'static', 'images')
    return images_dir

def get_placeholder_image_path():
    """Returns the path to the placeholder image."""
    return os.path.join(get_image_dir(), 'placeholder.png')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # Allowed image extensions for uploads

def allowed_file(filename):
    """Checks if a file's extension is in the list of allowed extensions."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_low_stock_threshold():
    """Retrieves the low stock threshold from environment variables, defaulting to 5."""
    try:
        # Use os.getenv to read from environment variables (loaded from .env)
        threshold_str = os.getenv("LOW_STOCK_THRESHOLD", "5")
        return int(threshold_str)
    except ValueError:
        st.warning("LOW_STOCK_THRESHOLD in .env is not a valid number. Using default: 5.")
        return 5

def get_currency_symbol():
    """Retrieves the currency symbol from environment variables, defaulting to '₹'."""
    # Use os.getenv to read from environment variables (loaded from .env)
    return os.getenv("CURRENCY_SYMBOL", "₹")

def get_default_admin_credentials():
    """Retrieves default admin username and password from environment variables."""
    default_username = os.getenv("DEFAULT_ADMIN_USERNAME")
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD")

    if not default_username or not default_password:
        st.error("Default admin credentials (DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD) not found in .env file.")
        st.stop() 
    return default_username, default_password

def ensure_dirs():
    """Ensures that necessary directories exist."""
    pdf_dir = get_pdf_dir()
    images_dir = get_image_dir()
    
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    # Create a placeholder image if it doesn't exist
    placeholder_path = get_placeholder_image_path()
    if not os.path.exists(placeholder_path):
        try:
            # A very minimal 1x1 transparent PNG. For a better visual, you should replace this with a proper image.
            # This is just to prevent errors if the file is missing.
            img = Image.new('RGBA', (1, 1), (255, 255, 255, 0)) # Transparent white 1x1 pixel
            img.save(placeholder_path)
            print(f"Created a dummy placeholder.png at: {placeholder_path}")
        except ImportError:
            print("Pillow not installed. Cannot generate placeholder.png. Please install Pillow (`pip install Pillow`) or manually place a `placeholder.png` in `static/images`.")
            # Fallback to creating an empty file if Pillow is not available
            with open(placeholder_path, 'w') as f:
                f.write("") # Create an empty file, which might cause issues but prevents FileNotFoundError
