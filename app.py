import streamlit as st

# Set page config (must be first Streamlit command)
st.set_page_config(page_title="🚀 Streamlit App", page_icon="🚀", layout="wide")

# Custom CSS for enhanced styling
st.markdown(
    """
    <style>
        /* Center align the sidebar content */
        [data-testid="stSidebar"] {
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .stButton>button {
            border-radius: 8px;
            background-color: #4CAF50;
            color: white;
            padding: 8px 16px;
            font-size: 16px;
            font-weight: bold;
            margin: 10px auto; /* Center align the buttons */
            height: 40px;
            width: 150px;
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

        /* Custom browser title styling */
        .streamlit-expanderHeader p {
            font-size: 16px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit App Title
st.markdown('<div class="header-text">🚀 Enhanced Streamlit App</div>', unsafe_allow_html=True)

# Use session state to track which button was clicked
if "active_page" not in st.session_state:
    st.session_state.active_page = "home"

# Sidebar Navigation
with st.sidebar:
    st.title("🧭 Navigation")

    # Home and Exit buttons (Top Section)
    st.write("")  # Spacer
    st.write("")  # Spacer
    home_col, exit_col = st.columns(2)
    with home_col:
        if st.button("🏠 Home", key="home_btn"):
            st.session_state.active_page = "home"
    with exit_col:
        if st.button("🚪 Exit", key="exit_btn"):
            st.session_state.active_page = "exit"

    st.write("---")  # Divider

    # Run Code 1 and Code 2 buttons (Bottom Section)
    code1_col, code2_col = st.columns(2)
    with code1_col:
        if st.button("⚙️ Run Code 1", key="code1_btn"):
            st.session_state.active_page = "code1"
    with code2_col:
        if st.button("🛠️ Run Code 2", key="code2_btn"):
            st.session_state.active_page = "code2"

# Display the selected page
if st.session_state.active_page == "home":
    # Home Page Content
    st.markdown(
        """
        <div class="section-box">
            <h2>Welcome to the 🚀 Enhanced Streamlit App!</h2>
            <p>Click on the navigation buttons to run Code 1 or Code 2. Each section will use the full screen for a better experience.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
elif st.session_state.active_page == "code1":
    # Full-Page Content for Code 1
    st.markdown('<div class="header-text">⚙️ Running Code 1</div>', unsafe_allow_html=True)
    st.write("This is where Code 1 will execute.")
    st.success("You are now viewing the full page for Code 1.")
    # Add your Code 1 functionality here
elif st.session_state.active_page == "code2":
    # Full-Page Content for Code 2
    st.markdown('<div class="header-text">🛠️ Running Code 2</div>', unsafe_allow_html=True)
    st.write("This is where Code 2 will execute.")
    st.success("You are now viewing the full page for Code 2.")
    # Add your Code 2 functionality here
elif st.session_state.active_page == "exit":
    st.markdown(
        '<div class="section-box"><h2>🚪 Exiting Application</h2><p>Thank you for using the app!</p></div>',
        unsafe_allow_html=True
    )
