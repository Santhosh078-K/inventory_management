import streamlit as st
import os
import uuid
import sys
from werkzeug.security import generate_password_hash # For initial admin user

# Add the base directory to sys.path to allow imports from other modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Import functions from other modules
# Note: db_operations is imported first to ensure dotenv is loaded and Mongo connection is attempted early.
from db_operations import load_users, add_user, find_user_by_username
from auth import login_page, register_page
from inventory_pages import show_inventory_page, add_item_page, edit_item_page
from admin_pages import admin_dashboard_page, manage_users_page, edit_user_page
from supplier_pages import show_supplier_management_page
from dashboard_pages import show_dashboard_page
from utils import ensure_dirs, get_default_admin_credentials

# --- Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    page_title="Inventory Management",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login' # Default page
if 'edit_item_id' not in st.session_state:
    st.session_state.edit_item_id = None
if 'edit_user_id' not in st.session_state:
    st.session_state.edit_user_id = None
# Set default theme to 'dark'
st.session_state.theme = 'dark'

# Ensure directories exist and paths are robustly initialized
ensure_dirs() # Call the function from utils module to set up directories

# Ensure default admin user exists
default_admin_username, default_admin_password = get_default_admin_credentials()
if not find_user_by_username(default_admin_username):
    hashed_password = generate_password_hash(default_admin_password)
    admin_user = {
        'username': default_admin_username,
        'password': hashed_password,
        'role': 'admin'
    }
    add_user(admin_user)
    st.success("Default admin user created. Please log in.")

# --- Custom CSS for Theming (Fixed to Dark Theme) ---
theme_css = f"""
<style>
    :root {{
        /* Dark Theme Variables */
        --primary-color: #66bb6a; /* Lighter green */
        --background-color: #262730; /* Dark grey */
        --text-color: #f0f2f6; /* Light grey */
        --card-background: #333333;
        --border-color: #444444;
        --sidebar-bg: #1a1a1a;
        --sidebar-text: #f0f2f6;
        --sidebar-header: #333333;
        --sidebar-header-text: #66bb6a;
        --button-hover: #5cb85c;
        --input-bg: #444444;
        --input-border: #555555;
        --table-header-bg: #444444;
        --table-border: #666666;
    }}

    /* Apply general styles to the body and main app container */
    body {{
        font-family: 'Inter', sans-serif;
        background-color: var(--background-color);
        color: var(--text-color);
    }}

    [data-testid="stAppViewContainer"] {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}
    
    /* Ensure all text elements inherit the main text color */
    [data-testid="stAppViewContainer"] *,
    [data-testid="stSidebar"] * {{
        color: var(--text-color) !important;
    }}

    /* Custom styles for inventory cards */
    .stCard {{
        background-color: var(--card-background);
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Darker shadow for dark theme */
        padding: 15px;
        margin-bottom: 20px;
        transition: transform 0.2s ease-in-out, background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
        border: 1px solid var(--border-color);
    }}

    .stCard:hover {{
        transform: translateY(-5px);
    }}
    .stCard.low-stock-item {{
        border: 2px solid #FF6347; /* Tomato red border */
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }}
    .stCard.low-stock-item .low-stock-text {{
        color: #FF6347 !important; /* Tomato red text */
        font-weight: bold;
        animation: pulse 1.5s infinite; /* Pulsing animation */
    }}
    @keyframes pulse {{
        0% {{ transform: scale(1); opacity: 1; }}
        50% {{ transform: scale(1.03); opacity: 0.8; }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}

    /* Streamlit's default alert styles (keeping original for consistency with Streamlit's internal styling) */
    .stAlert {{ border-radius: 8px; padding: 10px 15px; margin-bottom: 15px; }}
    .stAlert.stAlert--success {{ background-color: #d4edda; color: #155724; border-left: 5px solid #28a745; }}
    .stAlert.stAlert--info {{ background-color: #d1ecf1; color: #0c5460; border-left: 5px solid #17a2b8; }}
    .stAlert.stAlert--warning {{ background-color: #fff3cd; color: #856404; border-left: 5px solid #ffc107; }}
    .stAlert.stAlert--error {{ background-color: #f8d7da; color: #721c24; border-left: 5px solid #dc3545; }}

    /* Sidebar styling */
    [data-testid="stSidebar"] {{ /* Target the sidebar container */
        background-color: var(--sidebar-bg);
        transition: background-color 0.3s;
    }}

    /* Sidebar header/title */
    [data-testid="stSidebar"] .st-emotion-cache-1jmvejs {{ /* Target the Streamlit sidebar header */
        background-color: var(--sidebar-header);
        color: var(--sidebar-header-text) !important;
        padding: 15px;
        margin-bottom: 20px;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        transition: background-color 0.3s, color 0.3s;
    }}

    /* Sidebar buttons/links */
    [data-testid="stSidebar"] .stButton>button, 
    [data-testid="stSidebar"] .st-emotion-cache-1c7y2kl {{ /* Target default Streamlit buttons/links in sidebar */
        color: var(--sidebar-text) !important;
        transition: color 0.3s, background-color 0.3s;
    }}
    [data-testid="stSidebar"] .stButton>button:hover, 
    [data-testid="stSidebar"] .st-emotion-cache-1c7y2kl:hover {{
        background-color: rgba(255,255,255,0.05); /* Lighter hover for dark theme */
    }}

    /* Main content area (for general text and elements not explicitly styled) */
    [data-testid="stVerticalBlock"] {{ /* Target the main content container */
        background-color: var(--background-color);
        transition: background-color 0.3s;
    }}

    /* Buttons */
    .stButton>button {{
        background-color: var(--primary-color);
        color: var(--text-color) !important; /* Ensure button text is light grey for dark theme */
        border: none;
        border-radius: 5px;
        padding: 8px 15px;
        cursor: pointer;
        transition: background-color 0.3s;
    }}
    .stButton>button:hover {{
        background-color: var(--button-hover);
    }}

    /* Text inputs and select boxes */
    .stTextInput>div>div>input, 
    .stSelectbox>div>div>div, 
    .stTextArea>div>div>textarea, 
    .stNumberInput>div>div>input {{
        background-color: var(--input-bg);
        color: var(--text-color) !important;
        border: 1px solid var(--input-border);
        border-radius: 5px;
        padding: 8px 12px;
        transition: background-color 0.3s, color 0.3s, border-color 0.3s;
    }}
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--text-color) !important;
    }}

    /* Dataframes */
    .stDataFrame {{
        color: var(--text-color) !important;
    }}
    .stDataFrame .dataframe thead th {{
        background-color: var(--table-header-bg) !important;
        color: var(--text-color) !important;
        border-bottom: 1px solid var(--table-border) !important;
    }}
    .stDataFrame .dataframe tbody tr {{
        background-color: var(--card-background) !important;
    }}
    .stDataFrame .dataframe tbody tr:nth-child(odd) {{
        background-color: var(--background-color) !important;
    }}
    .stDataFrame .dataframe tbody td {{
        color: var(--text-color) !important;
        border-bottom: 1px solid var(--table-border) !important;
    }}

</style>
"""

st.markdown(theme_css, unsafe_allow_html=True)

# --- Sidebar Navigation ---
with st.sidebar:
    st.title("Inventory App")
    
    # Removed Theme Toggle Button
    st.markdown("---")

    if st.session_state.logged_in:
        st.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.role.capitalize()})")
        
        if st.button("Dashboard", key="nav_dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        if st.button("Inventory", key="nav_inventory"):
            st.session_state.current_page = 'inventory'
            st.rerun()
        if st.session_state.role == 'admin':
            if st.button("Add New Item", key="nav_add_item"):
                st.session_state.current_page = 'add_item'
                st.rerun()
            if st.button("Admin Dashboard", key="nav_admin_dashboard"):
                st.session_state.current_page = 'admin_dashboard'
                st.rerun()
            if st.button("Supplier Management", key="nav_supplier_management"):
                st.session_state.current_page = 'supplier_management'
                st.rerun()
        
        st.markdown("---")
        if st.button("Logout", key="nav_logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.current_page = 'login'
            st.success("You have been logged out.")
            st.rerun()
    else:
        st.write("Please log in or register.")
        if st.button("Login", key="nav_login"):
            st.session_state.current_page = 'login'
            st.rerun()
        if st.button("Register", key="nav_register"):
            st.session_state.current_page = 'register'
            st.rerun()

# --- Page Routing ---
if st.session_state.current_page == 'login':
    login_page()
elif st.session_state.current_page == 'register':
    register_page()
elif st.session_state.current_page == 'dashboard':
    show_dashboard_page()
elif st.session_state.current_page == 'inventory':
    show_inventory_page()
elif st.session_state.current_page == 'add_item':
    add_item_page()
elif st.session_state.current_page == 'edit_item':
    edit_item_page()
elif st.session_state.current_page == 'admin_dashboard':
    admin_dashboard_page()
elif st.session_state.current_page == 'manage_users':
    manage_users_page()
elif st.session_state.current_page == 'edit_user':
    edit_user_page()
elif st.session_state.current_page == 'supplier_management':
    show_supplier_management_page()
