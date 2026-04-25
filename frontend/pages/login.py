import streamlit as st

from api_client import login, register, get_me

def show():
    st.title("AI study assistant")

    tab1,tab2=st.tabs(["Login","Register"])

    with tab1:
        with st.form("login_form"):
            email=st.text_input("Email")
            password=st.text_input("Password",type="password")
            submitted=st.form_submit_button("Login")

            if submitted:
                try:
                    data=login(email,password)
                    
                    st.session_state.token=data["access_token"]

                    user=get_me(st.session_state.token)
                    st.session_state.user=user

                    st.success("Login successful")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")

    
    with tab2:
        with st.form("register_form"):
            name=st.text_input("Display Name")
            email=st.text_input("Email",key="reg_email")
            password=st.text_input("Password",type="password",key="reg_password")

            submitted=st.form_submit_button("Register")

            if submitted:
                try:
                    data=register(email,password,name)

                    st.session_state.token=data["access_token"]

                    user=get_me(st.session_state.token)
                    st.session_state.user=user

                    st.success("Registration successful!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))