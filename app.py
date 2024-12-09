# File path: app.py

import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.feedback import prompts
from trulens_eval import Feedback, Tru


# Initialize Trulens
openai_api_key = st.secrets["OPENAI_API_KEY"]
tru = Tru()
openai_provider = OpenAI(api_key=openai_api_key)


class TrulensFeedbackHandler:
    """
    Handles feedback using Trulens evaluation.
    Avoids unsupported dependencies like 'runnable'.
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
            # Simple evaluation mechanism via Trulens Feedback
            feedback = tru.evaluate_feedback({
                "prompt": prompt,
                "response": response
            })

            # If successful evaluation is performed, return computed score and explanation
            if feedback:
                score = feedback.feedback_score
                explanation = feedback.explanation
            else:
                score = 0.0
                explanation = "No evaluation logic returned feedback."
            return score, explanation

        except Exception as e:
            st.error(f"Error during feedback evaluation: {e}")
            return 0.0, "Error encountered while processing evaluation."


# Streamlit Application
def main():
    st.title("Trulens Feedback Application - User Data Evaluation")

    # Section for Excel file upload
    uploaded_file = st.file_uploader(
        "Upload your Excel file for processing and evaluation", type=["xlsx"]
    )

    if uploaded_file:
        # Read user-uploaded Excel data
        data = pd.read_excel(uploaded_file)
        st.write("Uploaded Data Preview:")
        st.dataframe(data)

        # Allow users to define custom prompts dynamically
        st.header("Define Your Feedback Logic")
        num_metrics = st.number_input(
            "How many metrics to evaluate?", min_value=1, step=1, value=1
        )

        user_metrics = {}
        for i in range(1, int(num_metrics) + 1):
            st.subheader(f"Metric {i}")
            selected_columns = st.multiselect(
                f"Select relevant columns for Metric {i}:",
                options=list(data.columns),
                key=f"metric{i}_columns"
            )
            user_prompt = st.text_input(
                f"Enter prompt logic for Metric {i}:",
                key=f"metric{i}_prompt"
            )

            if selected_columns and user_prompt:
                user_metrics[f"Metric {i}"] = {
                    "columns": selected_columns,
                    "prompt": user_prompt
                }

        # Execute feedback computation after user setup
        if st.button("Run Evaluation"):
            st.subheader("Processing feedback via Trulens")
            feedback_results = []
            trulens_handler = TrulensFeedbackHandler()

            for metric_name, metric_info in user_metrics.items():
                try:
                    # Process valid, non-empty contexts from provided columns
                    valid_data = data[metric_info["columns"]].dropna(how="any")
                    for idx, row in valid_data.iterrows():
                        combined_context = " ".join(row.astype(str))
                        
                        # Evaluate feedback using Trulens' evaluation mechanism
                        score, explanation = trulens_handler.evaluate(
                            prompt=metric_info["prompt"], response=combined_context
                        )

                        # Log feedback results
                        feedback_results.append({
                            "Metric": metric_name,
                            "Context": combined_context,
                            "Score": score,
                            "Explanation": explanation
                        })

                    # Convert results to DataFrame for visualization in Streamlit
                    feedback_df = pd.DataFrame(feedback_results)
                    st.write(feedback_df)

                    # Enable user to download results as a CSV file
                    csv_data = feedback_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_data,
                        file_name="feedback_results.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error evaluating '{metric_name}': {e}")


# Run the Streamlit app
if __name__ == "__main__":
    main()
