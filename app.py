import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.feedback import prompts
from trulens_eval import Feedback, Select, Tru, TruChain

# Ensure OpenAI API is available from secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]
feedback_provider = OpenAI(api_key=openai_api_key)

# Initialize Trulens for evaluation
tru = Tru()


class TrulensFeedbackHandler:
    """
    Class to encapsulate Trulens feedback logic.
    Dynamically evaluates feedback using Trulens.
    """
    def __init__(self):
        self.feedback_provider = feedback_provider

    def evaluate_feedback(self, prompt: str, response: str):
        """
        Evaluate prompt-response pair using Trulens evaluation.
        :param prompt: Input prompt string
        :param response: Response string from the Excel row or user input
        :return: Trulens evaluation score and explanation
        """
        try:
            # Evaluate feedback for the prompt-response pair
            evaluation_result = tru.evaluate_feedback({
                "prompt": prompt,
                "response": response,
            })
            # Extract evaluation results safely
            if evaluation_result:
                score = evaluation_result.feedback_score
                explanation = evaluation_result.explanation
            else:
                score = 0.0
                explanation = "No valid feedback."
            return score, explanation
        except Exception as e:
            st.error(f"Error processing feedback: {e}")
            return 0.0, "Error"


# Streamlit Application UI Logic
def main():
    # UI Title
    st.title("Excel-based Trulens Evaluation with Custom Metrics")

    # File Upload Section
    uploaded_file = st.file_uploader(
        "Upload your Excel file with data for evaluation", type=["xlsx"]
    )

    if uploaded_file:
        # Load uploaded Excel file into a DataFrame
        try:
            excel_data = pd.read_excel(uploaded_file)
            st.write("Preview of Uploaded Data:")
            st.dataframe(excel_data)

            # Input field for user-defined prompt logic
            user_prompt = st.text_input(
                "Define your custom prompt for feedback evaluation", 
                placeholder="Enter your prompt here"
            )

            if user_prompt and st.button("Evaluate Metrics"):
                # Run Trulens feedback logic here
                st.write("Processing Trulens feedback...")
                feedback_handler = TrulensFeedbackHandler()
                feedback_results = []

                # Iterate over rows dynamically
                for index, row in excel_data.iterrows():
                    try:
                        # Combine context or data dynamically
                        response_text = " ".join(row.dropna().astype(str))
                        score, explanation = feedback_handler.evaluate_feedback(
                            user_prompt, response_text
                        )

                        # Log feedback evaluation results
                        feedback_results.append({
                            "Row Index": index,
                            "Response": response_text,
                            "Score": score,
                            "Explanation": explanation
                        })
                    except Exception as e:
                        st.error(f"Failed on row {index}: {e}")
                        continue

                # Create feedback DataFrame for results visualization
                if feedback_results:
                    result_df = pd.DataFrame(feedback_results)
                    st.write("Feedback Results")
                    st.dataframe(result_df)

                    # Allow users to download results as CSV
                    csv_data = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_data,
                        file_name="feedback_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.write("No feedback results could be processed.")
            else:
                st.warning("Enter a prompt and click on 'Evaluate Metrics' to process data.")
        except Exception as e:
            st.error(f"Could not process uploaded file: {e}")
    else:
        st.info("Upload an Excel file to get started.")


# Trigger the app
if __name__ == "__main__":
    main()
