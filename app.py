import streamlit as st

# Custom CSS for better styling
st.markdown(
    """
    <style>
        /* Styling for buttons */
        .stButton>button {
            border-radius: 8px;
            background-color: #4CAF50;
            color: white;
            padding: 8px 16px; /* Reduced padding for smaller buttons */
            font-size: 16px;
            font-weight: bold;
            margin: 10px 5px;
            height: 40px; /* Uniform height */
            width: 150px; /* Uniform width */
            transition: background-color 0.3s ease, transform 0.2s ease;
        }

        .stButton>button:hover {
            background-color: #45a049;
            transform: scale(1.03);
        }

        .header-text {
            font-size: 30px;
            font-weight: bold;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 20px;
            color: #333333;
        }

        .section-box {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            background-color: #f9f9f9;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit App Title
st.markdown('<div class="header-text">Enhanced Streamlit App</div>', unsafe_allow_html=True)

# Use session state to track which button was clicked
if "active_page" not in st.session_state:
    st.session_state.active_page = "home"

# Sidebar Navigation
with st.sidebar:
    st.title("Navigation")
    col1, col2 = st.columns(2)  # Organize buttons side by side
    with col1:
        if st.button("Home", key="home_btn"):
            st.session_state.active_page = "home"
    with col2:
        if st.button("Run Code 1", key="code1_btn"):
            st.session_state.active_page = "code1"

    col3, col4 = st.columns(2)  # Second row of buttons side by side
    with col3:
        if st.button("Run Code 2", key="code2_btn"):
            st.session_state.active_page = "code2"
    with col4:
        if st.button("Exit", key="exit_btn"):
            st.session_state.active_page = "exit"

# Display the selected page
if st.session_state.active_page == "home":
    # Home Page Content
    st.markdown(
        """
        <div class="section-box">
            <h2>Welcome to the Enhanced Streamlit App!</h2>
            <p>Click on the sidebar buttons to run Code 1 or Code 2. Once you choose, the entire page will display the output.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
elif st.session_state.active_page == "code1":
    # Full-Page Content for Code 1
    st.markdown('<div class="header-text">Running Code 1</div>', unsafe_allow_html=True)
    st.write("This is where Code 1 will execute.")
    st.success("You are now viewing the full page for Code 1.")
    # Add your Code 1 functionality here
elif st.session_state.active_page == "code2":
    # Full-Page Content for Code 2
    st.markdown('<div class="header-text">Running Code 2</div>', unsafe_allow_html=True)
    st.write("This is where Code 2 will execute.")
    st.success("You are now viewing the full page for Code 2.")
    # Add your Code 2 functionality here
elif st.session_state.active_page == "exit":
    st.markdown(
        '<div class="section-box"><h2>Exiting Application</h2><p>Thank you for using the app!</p></div>',
        unsafe_allow_html=True
    )
