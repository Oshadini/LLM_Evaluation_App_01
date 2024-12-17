import streamlit as st

# Streamlit App Title
st.title("Streamlit App Template with Side-by-Side Buttons")

# Create two columns for side-by-side buttons
col1, col2 = st.columns(2)

# Button 1 in the first column
with col1:
    st.header("Section 1")
    if st.button("Run Code 1"):
        st.write("You clicked on 'Run Code 1'.")
        # Add the code for functionality 1 here
        # Example: st.write("Functionality 1 is running...")

# Button 2 in the second column
with col2:
    st.header("Section 2")
    if st.button("Run Code 2"):
        st.write("You clicked on 'Run Code 2'.")
        # Add the code for functionality 2 here
        # Example: st.write("Functionality 2 is running...")

# Optional Footer
st.write("---")
st.write("Edit this template to include your desired functionalities for each button.")
