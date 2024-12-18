import streamlit as st
import pandas as pd

# Define functions for processing each input format
def process_format_one(data):
    st.write("Processing File Format 1: 'Index, Question, Context, Answer, Reference Context, Reference Answer'")
    # Add your processing logic for Format 1 here
    st.dataframe(data.head())

def process_format_two(data):
    st.write("Processing File Format 2: 'Index, Conversation, Agent Prompt'")
    # Add your processing logic for Format 2 here
    st.dataframe(data.head())

# File upload section
st.title("File Format Detection and Processing Tool")
uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # Detect file type and read data
        if uploaded_file.name.endswith(".xlsx"):
            data = pd.read_excel(uploaded_file)
        else:
            data = pd.read_csv(uploaded_file)
        
        st.write("Preview of Uploaded Data:")
        st.dataframe(data.head())

        # Detect file format based on headers
        format_one_columns = {"Index", "Question", "Context", "Answer", "Reference Context", "Reference Answer"}
        format_two_columns = {"Index", "Conversation", "Agent Prompt"}

        if format_one_columns.issubset(data.columns):
            st.success("Detected File Format 1")
            process_format_one(data)
        elif format_two_columns.issubset(data.columns):
            st.success("Detected File Format 2")
            process_format_two(data)
        else:
            st.error("The uploaded file does not match the expected formats.")
    
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("Please upload a file to begin.")
