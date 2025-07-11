import streamlit as st
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
# Import MongoDB functions
from db_operations import load_users, add_user, find_user_by_username

def login_page():
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        # Remember Me checkbox is for UI only in Streamlit, actual session management is different
        remember_me = st.checkbox("Remember Me") 
        submitted = st.form_submit_button("Login")

        if submitted:
            # Use MongoDB function to find user
            user_data = find_user_by_username(username)

            if user_data and check_password_hash(user_data['password'], password):
                st.session_state.logged_in = True
                st.session_state.username = user_data['username']
                st.session_state.role = user_data['role']
                st.session_state.user_id_obj = user_data['_id'] # Store user ID from MongoDB
                st.session_state.current_page = 'dashboard' # Redirect to dashboard on successful login
                st.success(f"Logged in successfully as {st.session_state.username} ({st.session_state.role.capitalize()})!")
                st.rerun() # Rerun to update UI
            else:
                st.error("Invalid username or password.")

def register_page():
    st.subheader("Register")
    with st.form("register_form"):
        username = st.text_input("Username", key="reg_username")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        role = st.selectbox("Role", ["user"], key="reg_role")
        submitted = st.form_submit_button("Register")

        if submitted:
            if not username:
                st.error('Username is required.')
            elif not password or not confirm_password:
                st.error('Password and Confirm Password are required.')
            elif password != confirm_password:
                st.error('Passwords do not match.')
            elif len(password) < 6:
                st.error('Password must be at least 6 characters long.')
            else:
                # Use MongoDB function to check if username exists
                if find_user_by_username(username):
                    st.error('Username already exists. Please choose a different one.')
                else:
                    hashed_password = generate_password_hash(password)
                    new_user = {
                        'username': username,
                        'password': hashed_password,
                        'role': role
                    }
                    # Use MongoDB function to add new user
                    add_user(new_user)
                    st.success('Registration successful! You can now log in.')
                    st.session_state.current_page = 'login' # Redirect to login page
                    st.rerun() # Rerun to show login page
