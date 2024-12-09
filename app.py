# File path: app.py

import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.feedback import prompts
from trulens_eval import Feedback, Select, Tru, TruChain


# Initialize Trulens without invalid imports
openai_api_key = st.secrets["OPENAI_API_KEY"]
tru = Tru()
tru_chain = TruChain(steps=[OpenAI(api_key=openai_api_key)])


class TrulensFeedbackHandler:
    """
    Feedback handler class using Trulens for prompt/response evaluation.
    """
    def __init__(self):
        self.tru_chain = tru_chain

    def evaluate_feedback(self, prompt: str, generated_response: str):
        """
        Evaluate the prompt/response pair using Trulens.
        :param prompt: Prompt text.
        :param generated_response: Response text.
        :return: Feedback score & explanation using Trulens.
        """
        try:
            # Pass prompt-response pair to Trulens for evaluation
            feedback = self.tru_chain.invoke({
                "prompt": prompt,
                "response": generated_response
            })

            # Extract feedback results safely
            if feedback:
                score = feedback.feedback_score
                explanation = feedback.explanation
            else:
                score = 0.0
                explanation = "No feedback returned by Trulens."
            return score, explanation
        except Exception as e:
            st.error(f"Error during feedback computation: {e}")
            return 0.0, "Error evaluating feedback."


# Streamlit main application
def main():
    st.title("Custom Feedback Evaluation with Trulens")

    # File upload functionality
    uploaded_file = st.file_uploader(
        "Upload an Excel file to process data for analysis", type=["xlsx"]
    )

    if uploaded_file:
        # Parse the uploaded Excel file
        data = pd.read_excel(uploaded_file)
        st.write("Preview of uploaded data:")
        st.dataframe(data)

        # Allow the user to define the number of feedback metrics
        st.header("Define Feedback Metrics")
        num_metrics = st.number_input(
            "Number of feedback evaluations to perform", min_value=1, step=1, value=1
        )

        # Collect custom user-defined prompts and metrics
        metrics = {}
        for i in range(1, num_metrics + 1):
            st.subheader(f"Feedback Metric {i}")
            selected_columns = st.multiselect(
                f"Select data columns for metric {i}:", options=list(data.columns), key=f"metric{i}_columns"
            )
            user_prompt = st.text_input(
                f"Define a prompt for metric {i}:",
                key=f"metric{i}_prompt"
            )

            if selected_columns and user_prompt:
                metrics[f"Metric {i}"] = {
                    "columns": selected_columns,
                    "prompt": user_prompt
                }

        # Trigger Trulens feedback evaluation on click
        if st.button("Evaluate Feedback Metrics"):
            st.subheader("Processing Results using Trulens Feedback")
            results = []
            feedback_handler = TrulensFeedbackHandler()

            # Process each selected context/response pair for evaluation
            for metric_name, metric_info in metrics.items():
                try:
                    selected_data = data[metric_info["columns"]].dropna(how="any")
                    for index, row in selected_data.iterrows():
                        # Combine context from selected rows
                        combined_context = " ".join(row.astype(str))

                        # Evaluate feedback with Trulens
                        score, explanation = feedback_handler.evaluate_feedback(
                            prompt=metric_info["prompt"], generated_response=combined_context
                        )

                        # Store the result for visualization
                        results.append({
                            "Metric": metric_name,
                            "Context": combined_context,
                            "Score": score,
                            "Explanation": explanation
                        })

                    # Display results in Streamlit
                    result_df = pd.DataFrame(results)
                    st.write(result_df)

                    # Enable CSV export functionality
                    csv_data = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_data,
                        file_name="trulens_feedback_results.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error processing metric '{metric_name}': {e}")


# Run the Streamlit application
if __name__ == "__main__":
    main()
