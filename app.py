# File path: app.py

import streamlit as st
import pandas as pd
import openai
from trulens_eval import Tru, TruChain, Feedback
from trulens_eval.feedback.provider import OpenAI as TruOpenAI

# Initialize TruLens and OpenAI Feedback
openai.api_key = "your_openai_api_key"  # Replace with your OpenAI API key
tru = Tru()
feedback_provider = TruOpenAI(api_key=openai.api_key)

# Define custom feedback function
class CustomFeedback:
    @staticmethod
    def evaluate_prompt(prompt: str, generated: str) -> float:
        """
        Custom feedback function for evaluating the generated output based on the prompt.
        Returns a score between 0 and 1.
        """
        feedback_prompt = f"""
        Evaluate the following response for relevance and correctness based on the prompt:
        - Prompt: {prompt}
        - Generated Response: {generated}
        
        Score (0-1): 
        """
        try:
            result = feedback_provider.exact_match(prompt, generated)
            return result
        except Exception as e:
            st.warning(f"Feedback evaluation error: {e}")
            return 0.0


# Define the main function for the app
def main():
    st.title("Custom Metric Analysis Application with TruLens")

    # File upload section
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
    if uploaded_file:
        # Load the Excel file into a Pandas DataFrame
        data = pd.read_excel(uploaded_file)
        st.write("Preview of Uploaded File:")
        st.dataframe(data)

        # Get column names from the uploaded file
        columns = list(data.columns)

        # User input for metrics count
        st.header("Metric Selection")
        num_metrics = st.number_input("Enter the number of metrics you want to define:", min_value=1, step=1, value=1)

        metrics = {}

        # Allow user to define a custom number of metrics
        for i in range(1, num_metrics + 1):
            st.subheader(f"Metric {i}")
            selected_columns = st.multiselect(
                f"Select columns for Metric {i} (You can select multiple):",
                options=columns,
                key=f"metric_{i}_columns"
            )
            metric_prompt = st.text_input(
                f"Enter prompt for Metric {i}:",
                key=f"metric_{i}_prompt"
            )
            if selected_columns and metric_prompt:
                metrics[f"Metric {i}"] = {
                    "columns": selected_columns,
                    "prompt": metric_prompt
                }

        # Display the selected metrics
        st.subheader("Selected Metrics:")
        st.write(metrics)

        # Process and display metric scores and explanations
        if st.button("Generate Metric Scores"):
            st.subheader("Metric Scores and Explanations")
            results = []
            for metric_name, metric_info in metrics.items():
                # Generate OpenAI response for the metric prompt
                # Generate OpenAI response for the metric prompt
                # Generate OpenAI response for the metric prompt using the new API
                try:
                    response = openai.chat.completions.create(
                        model = "gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an assistant that evaluates content quality."},
                            {"role": "user", "content": metric_info['prompt']}
                        ],
                        max_tokens=100,
                        temperature=0.7
                    )
                    generated_text = response['choices'][0]['message']['content'].strip()
                except Exception as e:
                    generated_text = f"Error generating response: {e}"



                # Evaluate the generated text using custom feedback
                score = CustomFeedback.evaluate_prompt(metric_info['prompt'], generated_text)

                # Append the result
                results.append({
                    "Metric": metric_name,
                    "Selected Columns": ", ".join(metric_info["columns"]),
                    "Score": score,
                    "Explanation": generated_text
                })

            # Convert results to a DataFrame for display
            results_df = pd.DataFrame(results)
            st.write(results_df)

            # Allow the user to download the results
            csv_data = results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results as CSV",
                data=csv_data,
                file_name="metric_results.csv",
                mime="text/csv"
            )


# Run the app
if __name__ == "__main__":
    main()
