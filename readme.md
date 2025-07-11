Inventory Management System
This is a Streamlit-based Inventory Management System designed to help businesses efficiently track and manage their inventory, user accounts, and supplier information. It provides a user-friendly interface for various roles (Admin and User) to perform operations such as adding, editing, and deleting inventory items, managing users, and overseeing supplier details.

Features
User Authentication: Secure login and registration for different user roles.

Role-Based Access Control:

Admin: Full access to manage users, inventory, and suppliers.

User: View inventory, track quantities, and access dashboard metrics.

Dashboard Overview:

Key metrics: Total inventory items, total inventory value, low stock items.

Low stock alerts with options to notify suppliers or admin.

Inventory distribution by category.

Inventory Management:

Add new inventory items with details like name, category, quantity, and price.

Edit existing item details.

Delete items from inventory.

Generate and download PDF reports for individual items.

Search and filter inventory items.

Increment/decrement item quantities directly from the display.

User Management (Admin Only):

View all registered user accounts.

Edit user roles and usernames.

Reset user passwords.

Delete user accounts (with safeguards for the last admin).

Supplier Management (Admin Only):

Add new suppliers with contact details and categories supplied.

View, edit, and delete existing supplier information.

Link suppliers to inventory categories for targeted low-stock notifications.

Email Notifications: Automated low-stock alerts sent to relevant suppliers or the admin.

Dark Theme: The application is styled with a dark theme by default for a modern look.

Setup and Installation
Follow these steps to set up and run the application locally.

Prerequisites
Python 3.8+

MongoDB Atlas account (or a local MongoDB instance)

An email account (e.g., Gmail) to send notifications (requires app password for Gmail)

1. Clone the Repository
git clone <your-repository-url>
cd <your-repository-name>

2. Create a Virtual Environment (Recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Dependencies
Install the required Python packages using the requirements.txt file:

pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the root directory of your project (same level as app.py) and add the following variables. Do NOT commit this file to public repositories.

# MongoDB Connection
MONGO_URI="mongodb+srv://your_username:your_password@your_cluster_url/inventory?retryWrites=true&w=majority&appName=inventory"

# Admin Email for Notifications (e.g., a Gmail account)
ADMIN_EMAIL_ADDRESS="your_email@example.com"
ADMIN_EMAIL_PASSWORD="your_email_app_password" # Use an app password for Gmail, not your main password
EMAIL_SMTP_SERVER="smtp.gmail.com" # For Gmail
EMAIL_SMTP_PORT="465" # For SSL

# Application Settings
LOW_STOCK_THRESHOLD="10" # Quantity below which an item is considered low stock
CURRENCY_SYMBOL="₹" # Currency symbol to display (e.g., $, €, ₹)

# Default Admin User (used for initial setup if no admin exists)
DEFAULT_ADMIN_USERNAME="admin"
DEFAULT_ADMIN_PASSWORD="adminpassword" # Change this immediately after first login!

Important Notes for Email Configuration:

Gmail App Passwords: If you're using Gmail, you'll need to generate an "App password" instead of using your regular Gmail password. Go to your Google Account -> Security -> 2-Step Verification -> App passwords.

SMTP Server/Port: Adjust EMAIL_SMTP_SERVER and EMAIL_SMTP_PORT if you are using an email provider other than Gmail.

5. Run the Application
streamlit run app.py

Your Streamlit application will open in your web browser.

Usage
Initial Setup: On first run, a default admin user (username: admin, password: adminpassword) will be created. Log in with these credentials immediately and change the password.

Login/Register: Use the login page to access the system. New users can register, but only admins can manage roles.

Navigation: Use the sidebar to navigate between Dashboard, Inventory, Admin Dashboard, and Supplier Management pages.

Manage Inventory: Add new items, update quantities, edit details, and download PDF reports.

Admin Functions: Access "Admin Dashboard" and "Supplier Management" to manage users and suppliers.

Project Structure
.
├── app.py                  # Main Streamlit application file
├── auth.py                 # User authentication (login, registration)
├── admin_pages.py          # Admin dashboard and user management
├── dashboard_pages.py      # Main user dashboard with metrics and alerts
├── db_operations.py        # MongoDB database operations (CRUD for users, inventory, suppliers)
├── inventory_pages.py      # Inventory management (add, edit, delete, view items, PDF generation)
├── notification_service.py # Email notification functions (e.g., low stock alerts)
├── supplier_pages.py       # Supplier management (add, edit, delete, view suppliers)
├── utils.py                # Utility functions (directory setup, constants, env variable retrieval)
├── requirements.txt        # List of Python dependencies
├── .env.example            # Example .env file (DO NOT USE IN PRODUCTION, copy to .env)
└── static/                 # Static files (images, generated PDFs)
    ├── images/
    └── pdfs/

Contributing
Feel free to fork the repository, make improvements, and submit pull requests.

License
[Specify your license here, e.g., MIT License]