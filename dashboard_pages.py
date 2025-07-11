import streamlit as st
import pandas as pd
import re # Import regex for email validation

# Import MongoDB functions
from db_operations import get_all_inventory_items, get_all_suppliers, load_users, find_suppliers_by_category
from utils import get_low_stock_threshold, get_currency_symbol, ITEM_CATEGORIES
from notification_service import send_low_stock_notification

def is_valid_email(email):
    """Basic regex for email validation."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def show_dashboard_page():
    """Renders the main dashboard for inventory overview and reports."""
    if not st.session_state.logged_in:
        st.warning("Please log in to view the dashboard.")
        return

    st.subheader("Dashboard Overview")

    inventory = get_all_inventory_items() # Use MongoDB function
    users = load_users() # Use MongoDB function
    suppliers = get_all_suppliers() # Use MongoDB function
    low_stock_threshold = get_low_stock_threshold()
    currency_symbol = get_currency_symbol()

    # --- Key Metrics ---
    st.markdown("### Key Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Inventory Items", value=len(inventory))
    with col2:
        total_value = sum(item['quantity'] * item['price'] for item in inventory)
        st.metric(label="Total Inventory Value", value=f"{currency_symbol}{total_value:,.2f}")
    with col3:
        low_stock_items = [item for item in inventory if item['quantity'] <= low_stock_threshold]
        st.metric(label="Low Stock Items", value=len(low_stock_items))

    st.markdown("---")

    # --- Low Stock Alerts ---
    st.markdown("### Low Stock Alerts")
    if low_stock_items:
        for item in low_stock_items:
            selected_item_id = item['id'] # Use the 'id' field
            st.warning(f"Item **{item['name']}** is low in stock! Quantity: {item['quantity']}")
            
            # Option to notify supplier or admin
            item_category = item.get('category')
            if item_category:
                relevant_suppliers = find_suppliers_by_category(item_category)
                supplier_emails = [s['email'] for s in relevant_suppliers if s.get('email') and is_valid_email(s['email'])]
                supplier_names = [s['name'] for s in relevant_suppliers if s.get('email') and is_valid_email(s['email'])]

                if supplier_emails:
                    if st.button(f"Notify Supplier(s) for {item['name']}", key=f"dashboard_notify_supplier_{selected_item_id}"):
                        send_low_stock_notification(item, supplier_emails=supplier_emails, supplier_name=", ".join(supplier_names))
                        st.rerun()
                else:
                    st.info(f"No supplier with a valid email found for category '{item_category}'.")
                    if st.button(f"Notify Admin for {item['name']}", key=f"dashboard_notify_admin_{selected_item_id}"):
                        send_low_stock_notification(item) # Fallback to admin email
                        st.rerun()
            else:
                st.info(f"Item '{item['name']}' has no category. Cannot find specific supplier.")
                if st.button(f"Notify Admin for {item['name']}", key=f"dashboard_notify_admin_no_category_{selected_item_id}"):
                    send_low_stock_notification(item) # Fallback to admin email
                    st.rerun()
    else:
        st.info("No items are currently low in stock.")

    st.markdown("---")

    # --- Inventory Distribution by Category (Simple Chart/Table) ---
    st.markdown("### Inventory Distribution by Category")
    if inventory:
        # Ensure 'category' column exists, fill missing with 'N/A' for plotting
        inventory_df = pd.DataFrame(inventory)
        if 'category' not in inventory_df.columns:
            inventory_df['category'] = 'N/A'
        
        category_counts = inventory_df['category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Number of Items']
        st.dataframe(category_counts, hide_index=True, use_container_width=True)
        st.bar_chart(category_counts.set_index('Category'))
    else:
        st.info("No inventory data to display category distribution.")

    st.markdown("---")

    # --- User and Supplier Counts ---
    st.markdown("### System Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Users", value=len(users))
    with col2:
        st.metric(label="Total Suppliers", value=len(suppliers))

