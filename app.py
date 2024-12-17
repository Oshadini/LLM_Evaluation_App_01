import streamlit as st

# Streamlit App Title
st.title("Streamlit App Template with Two Buttons")

# Button 1 Section
st.header("Section 1: Run Functionality 1")
if st.button("Run Code 1"):
    st.write("You clicked on 'Run Code 1'.")
    # Add the code for functionality 1 here
    # Example: st.write("Functionality 1 is running...")

# Button 2 Section
st.header("Section 2: Run Functionality 2")
if st.button("Run Code 2"):
    st.write("You clicked on 'Run Code 2'.")
    # Add the code for functionality 2 here
    # Example: st.write("Functionality 2 is running...")

# Optional Footer
st.write("---")
st.write("Edit this template to include your desired functionalities for each button.")
