import streamlit as st
import pandas as pd
from trulens_eval.app import App
from trulens_eval.feedback.provider import Provider
from trulens_eval.feedback import Feedback
from trulens_eval.select import Select
from trulens_eval.session import TruSession

# Custom Feedback Provider Class
class CustomFeedback(Provider):
    def relevance_score(self, question: str, context: str, answer: str) -> float:
        """
        Custom feedback function to evaluate the relevance of an answer to the question and context.
        Args:
            question (str): The question being evaluated.
            context (str): The context provided for the question.
            answer (str): The answer to the question.
        Returns:
            float: A score between 0 (not relevant) and 1 (extremely relevant).
        """
        if not all([question, context, answer]):
            return 0.0

        relevance_prompt = (
            f"Evaluate the relevance of the answer to the question based on the context.\n"
            f"Question: {question}\n"
            f"Context: {context}\n"
            f"Answer: {answer}\n"
            f"Provide a relevance score between 0 (not relevant) and 1 (extremely relevant)."
        )
        
        return self.generate_score(system_prompt=relevance_prompt)

# Instantiate Custom Feedback Provider
custom_feedback = CustomFeedback()

# Initialize App
app = App(name="Relevance Scorer")

# Define Streamlit UI
st.set_page_config(page_title="Relevance Evaluation", page_icon="✅", layout="wide")
st.title("Relevance Evaluation with TruLens")

# File Upload
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    data = pd.read_excel(uploaded_file)

    st.write("### Uploaded Data")
    st.dataframe(data)

    # Check for required columns
    required_columns = ["Question", "Context", "Answer"]
    if not all(col in data.columns for col in required_columns):
        st.error(f"The uploaded file must include the columns: {', '.join(required_columns)}")
    else:
        st.success("File validated successfully!")

        # Placeholder for results
        results = []

        # Process each row
        for idx, row in data.iterrows():
            question = row.get("Question", "")
            context = row.get("Context", "")
            answer = row.get("Answer", "")

            # Define Feedback Function
            f_relevance = Feedback(custom_feedback.relevance_score).on(
                question=Select.Value(question),
                context=Select.Value(context),
                answer=Select.Value(answer)
            )

            # Evaluate Feedback
            session = TruSession()
            feedback_results = session.run_feedback_functions(
                record=None,  # Not using a specific record in this example
                feedback_functions=[f_relevance]
            )

            # Extract Results
            for feedback, result in feedback_results.items():
                results.append({
                    "Row": idx + 1,
                    "Score": result.result,
                    "Explanation": result.calls[0].meta.get("reason", "No explanation provided")
                })

        # Display Results
        st.write("### Evaluation Results")
        results_df = pd.DataFrame(results)
        st.dataframe(results_df)

        # Option to Download Results
        st.download_button(
            label="Download Results",
            data=results_df.to_csv(index=False),
            file_name="evaluation_results.csv",
            mime="text/csv"
        )
else:
    st.info("Please upload an Excel file with columns: Question, Context, and Answer.")
