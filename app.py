# File path: app.py

import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.feedback import prompts
from trulens_eval import Tru  # Avoid unsupported imports

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
            # Minimal feedback evaluation using Trulens
            evaluation_feedback = tru.evaluate_feedback({
                "prompt": prompt,
                "response": response,
            })

            # Extract feedback details safely
            if evaluation_feedback:
                score = evaluation_feedback.feedback_score
                explanation = evaluation_feedback.explanation
            else:
                score = 0.0
                explanation = "No valid evaluation provided."
            return score, explanation

        except Exception as e:
            st.error(f"Evaluation error: {e}")
            return 0.0, "Error during feedback evaluation"


# Streamlit Application
def main():
    st.title("Trulens Feedback Application - Data Evaluation")

    # Section for user file upload
    uploaded_file = st.file_uploader(
        "Upload your Excel file to process and evaluate metrics", type=["xlsx"]
    )

    if uploaded_file:
        # Read uploaded Excel
        data = pd.read_excel(uploaded_file)
        st.write("Preview of Uploaded Data:")
        st.dataframe(data)

        # User sets prompts and columns dynamically
        st.header("Define Your Metrics and Evaluation Logic")
        num_metrics = st.number_input(
            "How many metrics would you like to evaluate?", min_value=1, step=1, value=1
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
                f"Enter evaluation prompt for Metric {i}:",
                key=f"metric{i}_prompt"
            )

            if selected_columns and user_prompt:
                user_metrics[f"Metric {i}"] = {
                    "columns": selected_columns,
                    "prompt": user_prompt
                }

        # Trigger the feedback logic computation
        if st.button("Run Evaluation"):
            st.subheader("Processing feedback via Trulens")
            feedback_results = []
            trulens_handler = TrulensFeedbackHandler()

            for metric_name, metric_info in user_metrics.items():
                try:
                    # Process user input columns and ensure valid data
                    valid_data = data[metric_info["columns"]].dropna(how="any")
                    for idx, row in valid_data.iterrows():
                        combined_context = " ".join(row.astype(str))

                        # Evaluate using Trulens logic
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

                    # Convert results to a DataFrame for visualization
                    feedback_df = pd.DataFrame(feedback_results)
                    st.write(feedback_df)

                    # Allow users to download results
                    csv_data = feedback_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_data,
                        file_name="feedback_results.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error processing metric '{metric_name}': {e}")


# Execute the application
if __name__ == "__main__":
    main()
