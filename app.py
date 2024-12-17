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

# Create two columns for side-by-side buttons
col1, col2 = st.columns(2)

# Button 1 in the first column
with col1:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.header("Run Code 1")
    if st.button("Execute Code 1"):
        st.success("You clicked on 'Execute Code 1'.")
        # Add Code 1 Functionality Here
    st.markdown('</div>', unsafe_allow_html=True)

# Button 2 in the second column
with col2:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.header("Run Code 2")
    if st.button("Execute Code 2"):
        st.success("You clicked on 'Execute Code 2'.")
        # Add Code 2 Functionality Here
    st.markdown('</div>', unsafe_allow_html=True)

# Optional Footer
st.markdown('<div style="text-align:center; margin-top:50px;">'
            'Designed with ❤️ using <strong>Streamlit</strong></div>', unsafe_allow_html=True)
