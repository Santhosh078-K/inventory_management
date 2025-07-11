import streamlit as st
import pandas as pd
import uuid
import datetime
import re # Import regex for email validation

# Import MongoDB functions
from db_operations import (
    get_all_suppliers, add_supplier, update_supplier,
    delete_supplier, find_supplier_by_id, find_suppliers_by_category,
    get_all_inventory_items # Needed for low stock notifications
)
from notification_service import send_low_stock_notification
from utils import ITEM_CATEGORIES, get_low_stock_threshold

def is_valid_email(email):
    """Basic regex for email validation."""
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)

def show_supplier_management_page():
    """Renders the supplier management page for admins."""
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return

    st.subheader("Supplier Management")

    suppliers = get_all_suppliers() # Use MongoDB function

    # --- Add New Supplier ---
    st.markdown("### Add New Supplier")
    with st.form("add_supplier_form", clear_on_submit=True):
        supplier_name = st.text_input("Supplier Name")
        contact_person = st.text_input("Contact Person")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email Address")
        # Multi-select for categories supplied
        supplied_categories = st.multiselect(
            "Categories Supplied",
            options=ITEM_CATEGORIES,
            help="Select all categories this supplier provides."
        )
        address = st.text_area("Address")
        
        submitted = st.form_submit_button("Add Supplier")

        if submitted:
            if not supplier_name or not email:
                st.error('Supplier Name and Email are required.')
            elif not is_valid_email(email):
                st.error('Please enter a valid email address.')
            else:
                new_supplier_data = {
                    'name': supplier_name,
                    'contact_person': contact_person,
                    'phone': phone,
                    'email': email,
                    'categories': supplied_categories, # Save as list
                    'address': address,
                    'created_at': datetime.datetime.now().isoformat()
                }
                add_supplier(new_supplier_data) # Use MongoDB function
                st.success(f"Supplier '{supplier_name}' added successfully!")
                st.rerun() # Rerun to refresh the list

    st.markdown("---")

    # --- View and Manage Suppliers ---
    st.markdown("### Existing Suppliers")
    if suppliers:
        # Prepare data for display, converting list of categories to a readable string
        suppliers_display_data = []
        for s in suppliers:
            s_copy = s.copy()
            s_copy['Categories'] = ", ".join(s_copy.get('categories', [])) if s_copy.get('categories') else "N/A"
            s_copy['ID'] = str(s_copy['_id']) # Ensure ID is string for display
            suppliers_display_data.append(s_copy)

        suppliers_df = pd.DataFrame(suppliers_display_data)
        
        # Select relevant columns for display
        display_columns = ['ID', 'name', 'contact_person', 'phone', 'email', 'Categories', 'address']
        st.dataframe(suppliers_df[display_columns], hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Edit/Delete Supplier")

        supplier_options = {s['name']: str(s['_id']) for s in suppliers}
        selected_supplier_name = st.selectbox("Select Supplier", options=list(supplier_options.keys()), key="select_supplier_to_manage")
        selected_supplier_id = supplier_options[selected_supplier_name]

        supplier_to_edit = find_supplier_by_id(selected_supplier_id) # Use MongoDB function

        if supplier_to_edit:
            with st.form(f"edit_supplier_form_{selected_supplier_id}"):
                edited_name = st.text_input("Supplier Name", value=supplier_to_edit['name'], key=f"edit_name_{selected_supplier_id}")
                edited_contact_person = st.text_input("Contact Person", value=supplier_to_edit.get('contact_person', ''), key=f"edit_contact_{selected_supplier_id}")
                edited_phone = st.text_input("Phone Number", value=supplier_to_edit.get('phone', ''), key=f"edit_phone_{selected_supplier_id}")
                edited_email = st.text_input("Email Address", value=supplier_to_edit['email'], key=f"edit_email_{selected_supplier_id}")
                edited_supplied_categories = st.multiselect(
                    "Categories Supplied",
                    options=ITEM_CATEGORIES,
                    default=supplier_to_edit.get('categories', []),
                    key=f"edit_categories_{selected_supplier_id}"
                )
                edited_address = st.text_area("Address", value=supplier_to_edit.get('address', ''), key=f"edit_address_{selected_supplier_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    update_submitted = st.form_submit_button("Update Supplier")
                with col2:
                    delete_button = st.form_submit_button("Delete Supplier")

                if update_submitted:
                    if not edited_name or not edited_email:
                        st.error('Supplier Name and Email are required.')
                    elif not is_valid_email(edited_email):
                        st.error('Please enter a valid email address.')
                    else:
                        updates = {
                            'name': edited_name,
                            'contact_person': edited_contact_person,
                            'phone': edited_phone,
                            'email': edited_email,
                            'categories': edited_supplied_categories,
                            'address': edited_address
                        }
                        update_supplier(selected_supplier_id, updates) # Use MongoDB function
                        st.success(f"Supplier '{edited_name}' updated successfully!")
                        st.rerun()
                
                if delete_button:
                    # Add confirmation for deletion
                    if st.session_state.get(f'confirm_delete_supplier_{selected_supplier_id}', False):
                        delete_supplier_from_db(selected_supplier_id)
                        st.success(f"Supplier '{supplier_to_edit['name']}' deleted successfully!")
                        st.session_state[f'confirm_delete_supplier_{selected_supplier_id}'] = False # Reset confirmation
                        st.rerun()
                    else:
                        st.warning(f"Are you sure you want to delete supplier '{supplier_to_edit['name']}'? Click 'Confirm Delete' to proceed.")
                        st.session_state[f'confirm_delete_supplier_{selected_supplier_id}'] = True
                        # Provide a button to trigger the actual deletion
                        if st.form_submit_button("Confirm Delete", key=f"confirm_del_supplier_action_btn_{selected_supplier_id}"):
                            delete_supplier_from_db(selected_supplier_id)
                            st.success(f"Supplier '{supplier_to_edit['name']}' deleted successfully!")
                            st.session_state[f'confirm_delete_supplier_{selected_supplier_id}'] = False
                            st.rerun()
        else:
            st.info("Select a supplier to view/edit their details.")
    else:
        st.info("No suppliers added yet.")

    st.markdown("---")
    st.markdown("### Low Stock Items to Notify Suppliers")
    inventory = get_all_inventory_items()
    low_stock_threshold = get_low_stock_threshold()
    low_stock_items = [item for item in inventory if item['quantity'] <= low_stock_threshold]

    if low_stock_items:
        for item in low_stock_items:
            selected_item_id = item['id']
            st.warning(f"Item **{item['name']}** is low in stock! Quantity: {item['quantity']}")
            
            item_category = item.get('category')
            if item_category:
                relevant_suppliers = find_suppliers_by_category(item_category)
                supplier_emails = [s['email'] for s in relevant_suppliers if s.get('email') and is_valid_email(s['email'])]
                supplier_names = [s['name'] for s in relevant_suppliers if s.get('email') and is_valid_email(s['email'])]

                if supplier_emails:
                    st.info(f"Suppliers for '{item_category}': {', '.join(supplier_names) if supplier_names else 'None'}")
                    if st.button(f"Notify Supplier(s) for {item['name']}", key=f"notify_supplier_low_stock_{selected_item_id}"):
                        send_low_stock_notification(item, supplier_emails=supplier_emails, supplier_name=", ".join(supplier_names))
                        st.rerun()
                else:
                    st.info(f"No suppliers with valid emails found for category '{item_category}'.")
                    if st.button(f"Notify Admin for {item['name']}", key=f"notify_admin_from_supplier_page_{selected_item_id}"):
                        send_low_stock_notification(item) # Fallback to admin email
                        st.rerun()
            else: # This else is for 'if item_category:'
                st.info(f"Item '{item['name']}' has no category. Cannot find specific supplier.")
                if st.button(f"Notify Admin for {item['name']}", key=f"notify_admin_no_category_{selected_item_id}"):
                    send_low_stock_notification(item) # Fallback to admin email
                    st.rerun()
    else:
        st.info("No items are currently low in stock.")

def delete_supplier_from_db(supplier_id):
    """Deletes a supplier from the suppliers database."""
    delete_supplier(supplier_id) # Use MongoDB delete_supplier
