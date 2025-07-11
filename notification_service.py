import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file at the start
load_dotenv()

def _get_email_credentials():
    """Retrieves email credentials from environment variables."""
    try:
        admin_email = os.getenv("ADMIN_EMAIL_ADDRESS")
        admin_password = os.getenv("ADMIN_EMAIL_PASSWORD")
        smtp_server = os.getenv("EMAIL_SMTP_SERVER")
        smtp_port = os.getenv("EMAIL_SMTP_PORT") # Read as string, convert later

        # Convert port to int, handle potential errors
        try:
            smtp_port = int(smtp_port)
        except (ValueError, TypeError):
            st.error("EMAIL_SMTP_PORT in .env is missing or not a valid number.")
            return None, None, None, None
        
        if not all([admin_email, admin_password, smtp_server, smtp_port]):
            raise ValueError("One or more email configuration variables are missing in .env.")
            
        return admin_email, admin_password, smtp_server, smtp_port
    except (KeyError, ValueError) as e:
        st.error(f"Email configuration missing or invalid in .env file: {e}. Please add ADMIN_EMAIL_ADDRESS, ADMIN_EMAIL_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT to your .env.")
        return None, None, None, None

def send_email(to_email, subject, body, attachment_path=None, attachment_filename=None, sender_display_name="Inventory App"):
    """
    Sends an email using the configured SMTP server.
    Can send to a single email (string) or multiple (list of strings).
    """
    admin_email, admin_password, smtp_server, smtp_port = _get_email_credentials()

    if not all([admin_email, admin_password, smtp_server, smtp_port]):
        st.error("Email sending is not configured. Please check environment variables.")
        return False

    msg = MIMEMultipart()
    msg['From'] = f"{sender_display_name} <{admin_email}>"
    
    # Handle single or multiple recipients
    if isinstance(to_email, list):
        msg['To'] = ", ".join(to_email)
    else:
        msg['To'] = to_email

    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment_path and attachment_filename:
        try:
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=attachment_filename)
            part['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'
            msg.attach(part)
        except FileNotFoundError:
            st.error(f"Attachment file not found: {attachment_path}")
            return False
        except Exception as e:
            st.error(f"Error attaching file {attachment_filename}: {e}")
            return False

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(admin_email, admin_password)
            server.send_message(msg)
        return True
    except smtplib.SMTPAuthenticationError:
        st.error("Failed to authenticate with SMTP server. Check email username/password.")
        return False
    except smtplib.SMTPConnectError as e:
        st.error(f"Failed to connect to SMTP server: {e}. Check server address and port.")
        return False
    except Exception as e:
        st.error(f"An error occurred while sending email: {e}")
        return False

def send_low_stock_notification(item_data, supplier_emails=None, supplier_name=None):
    """
    Sends a low stock notification email for a given item.
    Prioritizes sending to specific supplier emails if provided,
    otherwise falls back to the admin email.
    """
    subject = f"Low Stock Alert: {item_data['name']}"
    body = (f"Dear Recipient,\n\n"
            f"This is an urgent low stock alert for the following item:\n\n"
            f"Item Name: {item_data['name']}\n"
            f"Category: {item_data.get('category', 'N/A')}\n"
            f"Current Quantity: {item_data['quantity']}\n\n"
            f"Please take necessary action to restock this item.\n\n"
            f"Regards,\nInventory Management System")

    recipients = []
    _sender_display_name = "Inventory App" # Default sender display name

    if supplier_emails and len(supplier_emails) > 0:
        recipients.extend(supplier_emails)
        if supplier_name:
            _sender_display_name = f"Inventory App ({supplier_name})"
    else:
        # Fallback to admin email if no specific supplier emails are provided or found
        admin_email, _, _, _ = _get_email_credentials()
        if admin_email:
            recipients.append(admin_email)
            st.warning("No specific supplier emails provided or found. Sending notification to admin email as fallback.")
            # If falling back to admin, set sender display name to "Inventory Admin"
            _sender_display_name = "Inventory Admin" 
        else:
            st.error("No recipient email addresses (supplier or admin) configured. Cannot send low stock notification.")
            return False

    # Use the local variable _sender_display_name
    if send_email(recipients, subject, body, sender_display_name=_sender_display_name):
        st.success(f"Low stock notification email sent to {', '.join(recipients)} for {item_data['name']}.")
        return True
    else:
        st.error(f"Failed to send low stock notification email for {item_data['name']}.")
        return False


def send_daily_report_email(admin_email, pdf_path, pdf_filename):
    """
    Sends the daily report PDF to the admin via email.
    """
    subject = f"Daily Inventory Report - {pdf_filename.replace('.pdf', '')}"
    body = (f"Dear Admin,\n\n"
            f"Please find attached your daily inventory report.\n\n"
            f"Regards,\nInventory Management System")
    
    if send_email(admin_email, subject, body, pdf_path, pdf_filename):
        st.success(f"Daily report email sent to {admin_email} with attachment '{pdf_filename}'.")
        return True
    else:
        st.error(f"Failed to send daily report email to {admin_email}.")
        return False
