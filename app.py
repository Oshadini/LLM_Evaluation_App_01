import streamlit as st

# Custom CSS for better styling
st.markdown(
    """
    <style>
        .stButton>button {
            border-radius: 12px;
            background-color: #4CAF50;
            color: white;
            padding: 12px 20px;
            font-size: 18px;
            font-weight: bold;
            margin: 10px 5px;
            transition: background-color 0.3s ease, transform 0.2s ease;
        }

        .stButton>button:hover {
            background-color: #45a049;
            transform: scale(1.05);
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
    if st.button("Home"):
        st.session_state.active_page = "home"
    if st.button("Run Code 1"):
        st.session_state.active_page = "code1"
    if st.button("Run Code 2"):
        st.session_state.active_page = "code2"

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
