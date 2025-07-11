import streamlit as st
import os
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import re # Import regex for email validation

# Import MongoDB functions
from db_operations import (
    get_all_inventory_items, add_inventory_item, update_inventory_item,
    delete_inventory_item, find_inventory_item_by_id, find_suppliers_by_category
)
# Import utility functions and constants
from utils import ITEM_CATEGORIES, get_pdf_dir, get_low_stock_threshold, get_currency_symbol, get_image_dir, get_placeholder_image_path, ALLOWED_EXTENSIONS, allowed_file
from notification_service import send_low_stock_notification

def is_valid_email(email):
    """Basic regex for email validation."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def generate_item_pdf(item_data, item_image_filename=None):
    """
    Generates a PDF for a given item, optionally including an image,
    and saves it to the static/pdfs directory.
    Returns the filename of the generated PDF.

    Expects item_data to already contain the item's 'id'.
    """
    pdf_dir = get_pdf_dir()
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)

    # Ensure 'id' is available before proceeding
    if 'id' not in item_data or not item_data['id']:
        raise ValueError("Item data must contain a valid 'id' for PDF generation.")

    # Use the item's 'id' for uniqueness in the filename
    pdf_filename = f"{item_data['name'].replace(' ', '_').replace('/', '-')}_{item_data['id'][:8]}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    currency_symbol = get_currency_symbol()

    # Title
    story.append(Paragraph(f"Inventory Item: {item_data['name']}", styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    # Image (if provided and exists)
    if item_image_filename:
        images_dir = get_image_dir()
        image_full_path = os.path.join(images_dir, item_image_filename)
        if os.path.exists(image_full_path):
            try:
                # Add image to PDF, scale to fit width while maintaining aspect ratio
                img = Image(image_full_path)
                # Set a max width for the image in PDF (e.g., 4 inches)
                max_width = 4 * inch
                aspect_ratio = img.drawHeight / img.drawWidth
                if img.drawWidth > max_width:
                    img.drawWidth = max_width
                    img.drawHeight = max_width * aspect_ratio
                
                story.append(img)
                story.append(Spacer(1, 0.1 * inch)) # Small space after image
            except Exception as e:
                print(f"Warning: Could not embed image '{item_image_filename}' into PDF: {e}")
                story.append(Paragraph(f"<i>(Image could not be embedded: {item_image_filename})</i>", styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))
        else:
            story.append(Paragraph(f"<i>(Image file not found: {item_image_filename})</i>", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
    else:
        story.append(Paragraph("<i>(No image provided for this item)</i>", styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))

    # Details
    story.append(Paragraph(f"<b>Item ID:</b> {item_data['id']}", styles['Normal']))
    story.append(Paragraph(f"<b>Category:</b> {item_data.get('category', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"<b>Quantity:</b> {item_data['quantity']}", styles['Normal']))
    story.append(Paragraph(f"<b>Price:</b> {currency_symbol}{item_data['price']:.2f}", styles['Normal']))
    story.append(Spacer(1, 0.4 * inch))

    story.append(Paragraph("This document provides details for the inventory item.", styles['Normal']))

    doc.build(story)
    return pdf_filename


def show_inventory_page():
    """Renders the main inventory display with search, filters, quantity controls, and PDF download."""
    st.subheader("Current Inventory")
    inventory = get_all_inventory_items() # Use MongoDB function
    
    pdf_dir = get_pdf_dir()
    images_dir = get_image_dir()
    low_stock_threshold = get_low_stock_threshold()
    currency_symbol = get_currency_symbol()

    # Filters and Search
    col1, col2 = st.columns([3,1])
    with col1:
        search_term = st.text_input("Search by name:", key="inventory_search").lower()
    with col2:
        selected_category = st.selectbox("Filter by category:", ["All"] + ITEM_CATEGORIES, key="category_filter")

    filtered_inventory = [item for item in inventory if search_term in item['name'].lower()]
    if selected_category != "All":
        filtered_inventory = [item for item in filtered_inventory if item.get('category') == selected_category]

    if filtered_inventory:
        num_columns = 3
        cols = st.columns(num_columns)
        
        col_idx = 0
        for item in filtered_inventory:
            with cols[col_idx]:
                is_low_stock = item['quantity'] <= low_stock_threshold
                item_display_class = "stCard low-stock-item" if is_low_stock else "stCard"
                
                st.markdown(f'<div class="{item_display_class}">', unsafe_allow_html=True)
                st.markdown(f"**{item['name']}**")
                
                # Display item image or placeholder
                item_image_filename = item.get('image_filename')
                if item_image_filename:
                    image_path = os.path.join(images_dir, item_image_filename)
                    if os.path.exists(image_path):
                        st.image(image_path, caption=item['name'], use_column_width=True)
                    else:
                        st.image(get_placeholder_image_path(), caption="Image not found", use_column_width=True)
                else:
                    st.image(get_placeholder_image_path(), caption="No image", use_column_width=True)

                if is_low_stock:
                    st.markdown('<p class="low-stock-text">LOW STOCK!</p>', unsafe_allow_html=True)
                    if st.session_state.role == 'admin':
                        item_category = item.get('category')
                        if item_category:
                            relevant_suppliers = find_suppliers_by_category(item_category)
                            
                            # Filter for suppliers with valid emails
                            supplier_emails = [s['email'] for s in relevant_suppliers if s.get('email') and is_valid_email(s['email'])]
                            supplier_names = [s['name'] for s in relevant_suppliers if s.get('email') and is_valid_email(s['email'])]
                            
                            if supplier_emails:
                                if st.button(f"Notify Supplier(s) for {item['name']}", key=f"dashboard_notify_supplier_{item['id']}"):
                                    # Pass the list of supplier emails to the notification service
                                    send_low_stock_notification(item, supplier_emails=supplier_emails, supplier_name=", ".join(supplier_names))
                                    st.rerun()
                            else:
                                st.info(f"No supplier with a valid email found for category '{item_category}'.")
                                # Fallback to admin notification if no suitable suppliers
                                if st.button(f"Notify Admin for {item['name']}", key=f"dashboard_notify_admin_{item['id']}"):
                                    send_low_stock_notification(item) # Fallback to admin email
                                    st.rerun()
                        else:
                            st.info(f"Item '{item['name']}' has no category. Cannot find specific supplier.")
                            # Fallback to admin notification if no category
                            if st.button(f"Notify Admin for {item['name']}", key=f"dashboard_notify_admin_{item['id']}"):
                                send_low_stock_notification(item) # Fallback to admin email
                                st.rerun()


                st.write(f"ID: `{item['id'][:8]}...`")
                st.write(f"Category: **{item.get('category', 'N/A')}**")
                st.write(f"Price: **{currency_symbol}{item['price']:.2f}**")
                
                current_quantity = item['quantity']
                col_q1, col_q2, col_q3 = st.columns([1,1.5,1])
                with col_q1:
                    if st.button("-", key=f"decrement_{item['id']}", disabled=(current_quantity <= 0)):
                        if current_quantity > 0:
                            current_quantity -= 1
                            update_inventory_item(item['id'], {'quantity': current_quantity})
                            st.success(f"Quantity for {item['name']} reduced to {current_quantity}.")
                            st.rerun()
                with col_q2:
                    st.write(f"Quantity: **{current_quantity}**")
                with col_q3:
                    if st.session_state.role == 'admin':
                        if st.button("+", key=f"increment_{item['id']}"):
                            current_quantity += 1
                            update_inventory_item(item['id'], {'quantity': current_quantity})
                            st.success(f"Quantity for {item['name']} increased to {current_quantity}.")
                            st.rerun()

                pdf_filename = item.get('pdf_filename')
                if pdf_filename:
                    pdf_path = os.path.join(pdf_dir, pdf_filename)
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="Download PDF",
                                data=pdf_file,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                key=f"download_pdf_{item['id']}"
                            )
                    else:
                        st.info("PDF not found (might need to edit & re-save item).")
                else:
                    st.info("No PDF available for this item.")
                
                if st.session_state.role == 'admin':
                    if st.button(f"Edit {item['name']}", key=f"edit_btn_{item['id']}"):
                        st.session_state.current_page = 'edit_item'
                        st.session_state.edit_item_id = item['id']
                        st.rerun()
                    
                    if st.button(f"Delete {item['name']}", key=f"del_btn_{item['id']}"):
                        # Use a session state variable for confirmation
                        if st.session_state.get(f'confirm_delete_item_{item["id"]}', False):
                            delete_item_from_db(item['id'])
                            st.success("Item deleted successfully!")
                            # Reset confirmation state
                            st.session_state[f'confirm_delete_item_{item["id"]}'] = False
                            st.rerun()
                        else:
                            st.warning(f"Are you sure you want to delete {item['name']}? Click 'Confirm Delete' below to proceed.")
                            # Set confirmation state
                            st.session_state[f'confirm_delete_item_{item["id"]}'] = True
                            # Provide a button to trigger the actual deletion
                            if st.button("Confirm Delete", key=f"confirm_del_action_btn_{item['id']}"):
                                delete_item_from_db(item['id'])
                                st.success("Item deleted successfully!")
                                st.session_state[f'confirm_delete_item_{item["id"]}'] = False
                                st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            col_idx = (col_idx + 1) % num_columns
    else:
        st.info("No items in inventory matching your search or filters.")
        if st.session_state.role == 'admin':
            if st.button("Add New Item"):
                st.session_state.current_page = 'add_item'
                st.rerun()

def delete_item_from_db(item_id):
    """Deletes an item from the inventory and its associated PDF/image files."""
    pdf_dir = get_pdf_dir()
    images_dir = get_image_dir()
    
    item_to_delete = find_inventory_item_by_id(item_id) # Use MongoDB function
    
    if item_to_delete:
        if item_to_delete.get('pdf_filename'):
            pdf_path = os.path.join(pdf_dir, item_to_delete['pdf_filename'])
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    print(f"Deleted PDF: {pdf_path}")
                except OSError as e:
                    st.error(f"Error deleting PDF file: {e}")
        
        if item_to_delete.get('image_filename'):
            image_path = os.path.join(images_dir, item_to_delete['image_filename'])
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"Deleted image: {image_path}")
                except OSError as e:
                    st.error(f"Error deleting image file: {e}")
        
        delete_inventory_item(item_id) # Use MongoDB function
    else:
        st.error("Item not found.")


def add_item_page():
    """Renders the form to add a new inventory item and handles its submission, generating a PDF."""
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return

    st.subheader("Add New Inventory Item")
    with st.form("add_item_form"):
        name = st.text_input("Item Name")
        category = st.selectbox("Category", ITEM_CATEGORIES, key="add_category")
        quantity = st.number_input("Quantity", min_value=1, value=1)
        price = st.number_input("Price", min_value=0.01, value=0.01, format="%.2f")
        # Removed: uploaded_image_file = st.file_uploader("Upload Item Image (Optional)", type=list(ALLOWED_EXTENSIONS))
        
        submitted = st.form_submit_button("Add Item")

        if submitted:
            if not name:
                st.error('Item Name is required.')
            else:
                item_image_filename = None # Image filename will always be None as upload is removed

                new_item_data = {
                    'name': name,
                    'category': category,
                    'quantity': quantity,
                    'price': price,
                    'pdf_filename': None, # Initialize as None
                    'image_filename': item_image_filename # Will be None
                }
                
                try:
                    inserted_id = add_inventory_item(new_item_data)
                    new_item_data['id'] = inserted_id
                    
                    pdf_filename = generate_item_pdf(new_item_data, item_image_filename) # item_image_filename is None
                    
                    update_inventory_item(inserted_id, {'pdf_filename': pdf_filename})
                    
                    st.success(f"Item '{name}' added successfully and PDF generated: {pdf_filename}!")
                except ValueError as ve:
                    st.error(f"Error during PDF generation: {ve}. Item might have been added without PDF.")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}. Item might have been added without PDF.")
                
                st.session_state.current_page = 'inventory'
                st.rerun()

def edit_item_page():
    """Renders the form to edit an existing inventory item and handles its submission, regenerating a PDF."""
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return
    
    item_id = st.session_state.get('edit_item_id')
    if not item_id:
        st.warning("No item selected for editing. Please select an item from the inventory.")
        if st.button("Go to Inventory"):
            st.session_state.current_page = 'inventory'
            st.rerun()
        return

    item_to_edit = find_inventory_item_by_id(item_id) # Use MongoDB function

    if not item_to_edit:
        st.error("Item not found.")
        st.session_state.current_page = 'inventory'
        st.rerun()
        return

    st.subheader(f"Edit Inventory Item: {item_to_edit['name']}")
    with st.form("edit_item_form"):
        name = st.text_input("Item Name", value=item_to_edit['name'])
        
        current_category = item_to_edit.get('category', 'Other')
        display_categories = list(ITEM_CATEGORIES)
        if current_category not in display_categories:
            display_categories.append(current_category)
            
        current_category_index = display_categories.index(current_category)
        
        category = st.selectbox("Category", display_categories, index=current_category_index, key="edit_category")
        
        quantity = st.number_input("Quantity", min_value=1, value=item_to_edit['quantity'])
        price = st.number_input("Price", min_value=0.01, value=item_to_edit['price'], format="%.2f")
        
        st.write("---")
        st.markdown("##### Current Image:")
        current_image_filename = item_to_edit.get('image_filename')
        images_dir = get_image_dir()

        if current_image_filename:
            image_path = os.os.path.join(images_dir, current_image_filename)
            if os.path.exists(image_path):
                st.image(image_path, caption="Current Image", width=150)
                st.write(f"Filename: `{current_image_filename}`")
            else:
                st.info("Current image file not found.")
                st.image(get_placeholder_image_path(), caption="Image Missing", width=100)
        else:
            st.info("No current image.")
            st.image(get_placeholder_image_path(), caption="No Image", width=100)

        # Removed: uploaded_image_file = st.file_uploader("Upload New Item Image (Optional)", type=list(ALLOWED_EXTENSIONS), key="edit_file_uploader")
        
        submitted = st.form_submit_button("Update Item")

        if submitted:
            if not name:
                st.error('Item Name is required.')
            else:
                old_pdf_filename = item_to_edit.get('pdf_filename')
                # No longer need old_image_filename for deletion upon new upload

                updates = {
                    'name': name,
                    'category': category,
                    'quantity': quantity,
                    'price': price
                }
                
                # No new image upload to handle, retain existing image_filename
                updates['image_filename'] = item_to_edit.get('image_filename')

                # Update the item_to_edit dictionary with new values for PDF generation
                item_to_edit.update(updates)
                
                try:
                    new_pdf_filename = generate_item_pdf(item_to_edit, item_to_edit['image_filename'])
                    updates['pdf_filename'] = new_pdf_filename
                    st.success(f"PDF regenerated: {new_pdf_filename}")

                    old_pdf_filename = item_to_edit.get('pdf_filename')
                    if old_pdf_filename and old_pdf_filename != new_pdf_filename:
                        old_pdf_path = os.path.join(get_pdf_dir(), old_pdf_filename)
                        if os.path.exists(old_pdf_path):
                            try:
                                os.remove(old_pdf_path)
                                st.info(f"Old PDF '{old_pdf_filename}' deleted.")
                            except OSError as e:
                                st.error(f"Error deleting old PDF file: {e}")

                except Exception as e:
                    st.error(f"Error regenerating PDF: {e}. Item updated, but PDF might be outdated.")
                    updates['pdf_filename'] = item_to_edit.get('pdf_filename')

                update_inventory_item(item_id, updates) # Use MongoDB function
                st.success('Item updated successfully!')
                st.session_state.current_page = 'inventory'
                st.rerun()

