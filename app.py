# app.py
import streamlit as st
import pandas as pd

# Function to process the metrics
def calculate_metrics(data, selected_columns, custom_prompt):
    """Calculate metric scores and explanations based on selected columns and custom prompt."""
    metric_score = f"Score based on {', '.join(selected_columns)} and prompt: '{custom_prompt}'"
    explanation = f"Explanation for {', '.join(selected_columns)} using prompt: '{custom_prompt}'"
    return metric_score, explanation

# Streamlit App
st.title("Custom Metrics Generator")

# File upload section
uploaded_file = st.file_uploader("Upload an Excel file with the required structure", type=["xlsx"])
if uploaded_file:
    # Load the uploaded file into a dataframe
    df = pd.read_excel(uploaded_file)
    st.write("Uploaded Data Preview:")
    st.write(df)

    # Initialize metrics list
    metrics = []

    st.sidebar.title("Metrics Configuration")
    st.sidebar.write("Add multiple metrics by selecting columns and entering prompts.")

    # Number of metrics to configure
    num_metrics = st.sidebar.number_input("Number of Metrics", min_value=1, value=1, step=1)

    for i in range(num_metrics):
        st.sidebar.subheader(f"Metric {i + 1}")
        selected_columns = st.sidebar.multiselect(
            f"Select columns for Metric {i + 1}", options=df.columns.tolist(), key=f"columns_{i}"
        )
        custom_prompt = st.sidebar.text_input(
            f"Custom Prompt for Metric {i + 1}", key=f"prompt_{i}"
        )
        if selected_columns and custom_prompt:
            metrics.append((selected_columns, custom_prompt))

    if st.button("Generate Metrics"):
        # Generate table for metrics
        result_data = []

        for i, (columns, prompt) in enumerate(metrics):
            score, explanation = calculate_metrics(df, columns, prompt)
            result_data.append({
                "Metric": f"Metric {i + 1}",
                "Selected Columns": ", ".join(columns),
                "Custom Prompt": prompt,
                "Score": score,
                "Explanation": explanation
            })

        # Convert result data to DataFrame for display
        result_df = pd.DataFrame(result_data)
        st.write("Metric Results:")
        st.write(result_df)

        # Allow download of results
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df_to_csv(result_df)
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="metric_results.csv",
            mime="text/csv",
        )
