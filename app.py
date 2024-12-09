# File path: app.py

import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.feedback import prompts
from trulens_eval import Feedback, Select, Tru


# Initialize Trulens
openai_api_key = st.secrets["OPENAI_API_KEY"]
tru = Tru()
openai_provider = OpenAI(api_key=openai_api_key)


class TrulensFeedbackHandler:
    """
    Handles feedback using Trulens evaluation based solely on user-provided input.
    """
    def __init__(self):
        self.feedback_provider = openai_provider

    def evaluate(self, prompt: str, response: str):
        """
        Evaluate a prompt-response pair using Trulens feedback logic.
        :param prompt: The user-provided prompt.
        :param response: The context/response pair from data.
        :return: Feedback evaluation score and explanation.
        """
        try:
            # Direct feedback computation using Trulens
            feedback = tru.evaluate_feedback({
                "prompt": prompt,
                "response": response
            })

            if feedback:
                score = feedback.feedback_score
                explanation = feedback.explanation
            else:
                score = 0.0
                explanation = "No evaluation returned by Trulens."
            return score, explanation

        except Exception as e:
            st.error(f"Error evaluating response: {e}")
            return 0.0, "Trulens encountered an issue during evaluation."


# Streamlit Application
def main():
    st.title("Trulens Feedback Application - User Data Evaluation")

    # Section for Excel upload
    uploaded_file = st.file_uploader(
        "Upload your Excel file to analyze user data.", type=["xlsx"]
    )

    if uploaded_file:
        # Read uploaded Excel file
        data = pd.read_excel(uploaded_file)
        st.write("Uploaded Data Preview:")
        st.dataframe(data)

        # Allow users to define prompt logic dynamically
        st.header("Define Feedback Prompts")
        num_metrics = st.number_input(
            "How many feedback prompts would you like to define?", min_value=1, step=1, value=1
        )

        user_metrics = {}
        for i in range(1, int(num_metrics) + 1):
            st.subheader(f"Feedback Metric {i}")
            selected_columns = st.multiselect(
                f"Select relevant columns for Metric {i}:",
                options=list(data.columns),
                key=f"metric{i}_columns"
            )
            user_prompt = st.text_input(
                f"Define a prompt for Metric {i}:",
                key=f"metric{i}_prompt"
            )

            if selected_columns and user_prompt:
                user_metrics[f"Metric {i}"] = {
                    "columns": selected_columns,
                    "prompt": user_prompt
                }

        # Trigger analysis after user sets up feedback prompts
        if st.button("Process and Evaluate"):
            st.subheader("Running Analysis with Trulens Feedback")
            feedback_results = []
            trulens_handler = TrulensFeedbackHandler()

            # Loop over user-defined metrics and process their input context
            for metric_name, metric_info in user_metrics.items():
                try:
                    # Process only valid data rows (drop NaN entries)
                    filtered_data = data[metric_info["columns"]].dropna(how="any")
                    for index, row in filtered_data.iterrows():
                        # Combine context data into a single string
                        combined_context = " ".join(row.astype(str))
                        # Evaluate using Trulens feedback mechanism
                        score, explanation = trulens_handler.evaluate(
                            prompt=metric_info["prompt"], response=combined_context
                        )

                        # Store the evaluation results
                        feedback_results.append({
                            "Metric": metric_name,
                            "Context": combined_context,
                            "Score": score,
                            "Explanation": explanation
                        })

                    # Convert results to DataFrame for visualization
                    results_df = pd.DataFrame(feedback_results)
                    st.write(results_df)

                    # Provide CSV download option to user
                    csv_data = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Feedback Results as CSV",
                        data=csv_data,
                        file_name="feedback_results.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error processing metric '{metric_name}': {e}")


# Execute Streamlit app
if __name__ == "__main__":
    main()
