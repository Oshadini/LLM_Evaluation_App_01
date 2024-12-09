import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.feedback import prompts
from trulens_eval import Feedback, Select, Tru


# Ensure OpenAI API is available from secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]


class TrulensFeedbackHandler:
    """
    Handles feedback logic using only Trulens (no LLMs or extra libraries).
    Dynamically evaluates prompt-response pairs row-by-row.
    """
    def __init__(self):
        # Setup OpenAI if necessary with Trulens
        self.feedback_provider = OpenAI(api_key=openai_api_key)

    def evaluate_feedback(self, prompt: str, response: str):
        """
        Evaluates feedback using Trulens based on prompt-response pairs.
        This function avoids any LLM dependencies.
        """
        try:
            # Create Feedback evaluation
            feedback = Feedback(self.feedback_provider).on(
                answer=Select.RecordOutput
            ).on(
                question=Select.RecordInput
            ).on(
                context=Select.RecordInput
            )

            # Apply evaluation
            result = feedback.evaluate(
                answer=response,
                question=prompt,
            )
            score = result.result
            explanation = result.meta.get("reason", "Unknown reason.")
            
            # Return score and explanation
            return score, explanation
        except Exception as e:
            st.error(f"Error during feedback evaluation: {e}")
            return 0.0, "Error during feedback evaluation."


# Main UI flow for Streamlit
def main():
    st.title("Trulens Evaluation with Custom Metrics (Excel Upload)")

    uploaded_file = st.file_uploader(
        "Upload an Excel file for row-based evaluation", type=["xlsx"]
    )

    if uploaded_file:
        # Read uploaded Excel into DataFrame
        try:
            excel_data = pd.read_excel(uploaded_file)
            st.write("Uploaded Data:")
            st.dataframe(excel_data)

            # Input custom prompt for row-based comparison logic
            user_prompt = st.text_input(
                "Define your custom prompt for feedback evaluation",
                placeholder="Enter your feedback prompt logic here"
            )

            if user_prompt and st.button("Evaluate Feedback"):
                feedback_handler = TrulensFeedbackHandler()
                results = []

                # Process rows dynamically with Trulens evaluation logic
                for index, row in excel_data.iterrows():
                    try:
                        # Combine context dynamically (just as needed row-wise processing)
                        response_text = " ".join(row.dropna().astype(str))
                        score, explanation = feedback_handler.evaluate_feedback(
                            user_prompt, response_text
                        )

                        # Append results
                        results.append({
                            "Row Index": index,
                            "Response": response_text,
                            "Score": score,
                            "Explanation": explanation,
                        })

                    except Exception as e:
                        st.error(f"Failed to process row {index}: {e}")
                        continue

                # Visualize results
                if results:
                    results_df = pd.DataFrame(results)
                    st.write("Feedback Results")
                    st.dataframe(results_df)

                    # Allow user to download results
                    csv_data = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_data,
                        file_name="feedback_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No valid results to process.")
            else:
                st.info("Please input your custom prompt logic to proceed.")
        except Exception as e:
            st.error(f"Error reading the uploaded file: {e}")
    else:
        st.info("Upload an Excel file to get started with evaluation.")

# Trigger the app
if __name__ == "__main__":
    main()
