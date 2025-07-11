import streamlit as st
import pandas as pd
# Corrected import: Changed load_inventory to get_all_inventory_items
from db_operations import load_users, get_all_inventory_items, delete_user, find_user_by_id, update_user # Removed save_users
from werkzeug.security import generate_password_hash # For password hashing in edit user

def admin_dashboard_page():
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return

    st.subheader("Admin Dashboard")
    users = load_users()
    inventory = get_all_inventory_items() # Use get_all_inventory_items

    st.write(f"Welcome to the admin panel, **{st.session_state.username}**!")

    st.markdown("---")
    st.markdown("#### User Management")
    st.write("View, edit, and delete user accounts.")
    if st.button("Manage Users", key="btn_manage_users"):
        st.session_state.current_page = 'manage_users'
        st.rerun()

    st.markdown("---")
    st.markdown("#### Inventory Overview")
    st.write(f"Total Inventory Items: **{len(inventory)}**")
    if st.button("Add New Inventory Item", key="btn_add_inventory_item"):
        st.session_state.current_page = 'add_item'
        st.rerun()

def manage_users_page():
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return

    st.subheader("Manage Users")
    users = load_users() # Use MongoDB load_users

    if users:
        # Create a DataFrame for display
        users_df = pd.DataFrame([
            {'ID': str(user['_id']), 'Username': user['username'], 'Role': user['role']}
            for user in users
        ])
        st.dataframe(users_df, hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Edit/Delete User")

        # Dropdown to select user for editing/deletion
        user_options = {user['username']: str(user['_id']) for user in users}
        selected_username = st.selectbox("Select User", options=list(user_options.keys()), key="select_user_to_manage")
        selected_user_id = user_options[selected_username]

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Edit {selected_username}", key=f"edit_user_{selected_user_id}"):
                st.session_state.current_page = 'edit_user'
                st.session_state.edit_user_id = selected_user_id
                st.rerun()
        with col2:
            if st.button(f"Delete {selected_username}", key=f"delete_user_{selected_user_id}"):
                # Add confirmation for deletion
                if st.session_state.get(f'confirm_delete_user_{selected_user_id}', False):
                    # Prevent deleting the only admin account
                    user_to_delete = find_user_by_id(selected_user_id)
                    if user_to_delete and user_to_delete['role'] == 'admin':
                        admin_count = sum(1 for u in users if u['role'] == 'admin')
                        if admin_count == 1:
                            st.error("You cannot delete the only administrator account.")
                            st.session_state[f'confirm_delete_user_{selected_user_id}'] = False # Reset confirmation
                            st.rerun()
                            return

                    delete_user(selected_user_id) # Use MongoDB delete_user
                    st.success(f"User '{selected_username}' deleted successfully!")
                    st.session_state[f'confirm_delete_user_{selected_user_id}'] = False # Reset confirmation
                    st.rerun()
                else:
                    st.warning(f"Are you sure you want to delete user '{selected_username}'? Click 'Confirm Delete' to proceed.")
                    st.session_state[f'confirm_delete_user_{selected_user_id}'] = True
                    # Provide a button to trigger the actual deletion
                    if st.button("Confirm Delete", key=f"confirm_del_user_action_btn_{selected_user_id}"):
                        user_to_delete = find_user_by_id(selected_user_id)
                        if user_to_delete and user_to_delete['role'] == 'admin':
                            admin_count = sum(1 for u in users if u['role'] == 'admin')
                            if admin_count == 1:
                                st.error("You cannot delete the only administrator account.")
                                st.session_state[f'confirm_delete_user_{selected_user_id}'] = False # Reset confirmation
                                st.rerun()
                                return

                        delete_user(selected_user_id)
                        st.success(f"User '{selected_username}' deleted successfully!")
                        st.session_state[f'confirm_delete_user_{selected_user_id}'] = False
                        st.rerun()
    else:
        st.info("No users registered yet.")

    if st.button("Back to Admin Dashboard", key="back_to_admin_dashboard_from_manage_users"):
        st.session_state.current_page = 'admin_dashboard'
        st.rerun()

def edit_user_page():
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return

    user_id = st.session_state.get('edit_user_id')
    if not user_id:
        st.warning("No user selected for editing. Please select a user from 'Manage Users'.")
        if st.button("Go to Manage Users"):
            st.session_state.current_page = 'manage_users'
            st.rerun()
        return

    user_to_edit = find_user_by_id(user_id) # Use MongoDB find_user_by_id

    if not user_to_edit:
        st.error("User not found.")
        st.session_state.current_page = 'manage_users'
        st.rerun()
        return

    st.subheader(f"Edit User: {user_to_edit['username']}")
    users = load_users() # Load all users to check for duplicate usernames

    with st.form("edit_user_form"):
        new_username = st.text_input("Username", value=user_to_edit['username'], key="edit_username")
        new_role = st.selectbox("Role", ["admin", "user"], index=["admin", "user"].index(user_to_edit['role']), key="edit_role")
        new_password = st.text_input("New Password (leave blank to keep current)", type="password", key="edit_password")
        
        submitted = st.form_submit_button("Update User")

        if submitted:
            # Prevent demoting the only admin
            if user_to_edit['role'] == 'admin' and new_role == 'user':
                admin_count = sum(1 for u in users if u['role'] == 'admin')
                if admin_count == 1:
                    st.error("You cannot demote the only administrator account.")
                    st.stop()
            
            # Check for duplicate username if the username is changed
            if new_username.lower() != user_to_edit['username'].lower():
                if any(u['username'].lower() == new_username.lower() for u in users if str(u['_id']) != user_id): # Compare against other user IDs
                    st.error('Username already exists. Please choose a different one.')
                    st.stop()
            
            updates = {
                'username': new_username,
                'role': new_role
            }
            if new_password:
                if len(new_password) < 6:
                    st.error('New password must be at least 6 characters long.')
                    st.stop()
                updates['password'] = generate_password_hash(new_password) # Hash the new password

            update_user(user_id, updates) # Use update_user from db_operations
            st.success(f'User "{new_username}" updated successfully!')
            st.session_state.current_page = 'manage_users'
            st.rerun()

    if st.button("Back to Manage Users", key="back_to_manage_users_from_edit"):
        st.session_state.current_page = 'manage_users'
        st.rerun()
