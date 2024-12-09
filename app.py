import streamlit as st
import pandas as pd
from typing import Optional, Dict, Tuple
from trulens_eval import Feedback, Select, TruSession, App
from trulens_eval.feedback.provider import OpenAI


# Define a custom provider with a feedback function
class CustomFeedBackFunction(OpenAI):
    def custom_metric_score(self, answer: Optional[str] = None, question: Optional[str] = None, context: Optional[str] = None) -> Tuple[float, Dict]:
        """
        A function that evaluates the relevance of an answer, question, and context.
        Args:
            answer (str): The answer being evaluated.
            question (str): The question being evaluated.
            context (str): The context provided.

        Returns:
            Tuple[float, Dict]: Score between 0-1 and the reasoning.
        """
        professional_prompt = """
        Rate the relevance on a scale from 0 (not at all related) to 10 (extremely related):
        """
        if answer:
            professional_prompt += f"Answer: {answer}\n"
        if question:
            professional_prompt += f"Question: {question}\n"
        if context:
            professional_prompt += f"Context: {context}\n"

        return self.generate_score_and_reasons(
            system_prompt="RELEVANCE",
            user_prompt=professional_prompt
        )


# Initialize TruLens App with minimal required context.
app = App(
    name="custom_feedback_ui",
    module="custom_feedback_ui_module",  # This should be a name that represents your current module
)


# Streamlit UI
st.set_page_config(
    page_title="Custom LLM Evaluation with TruLens",
    page_icon="📊",
    layout="wide",
)

st.title("Evaluate with Custom Metrics Using TruLens")

# File uploader for user to upload Excel with Question, Context, Answer
uploaded_file = st.file_uploader(
    "Upload an Excel file with 'Question', 'Answer', and 'Context' columns", type=["xlsx"]
)

if uploaded_file:
    # Read uploaded data
    data = pd.read_excel(uploaded_file)
    st.write("Uploaded Data:")
    st.dataframe(data)

    # Ensure required columns exist
    required_columns = ["Question", "Answer", "Context"]
    if not all(col in data.columns for col in required_columns):
        st.error(
            f"The uploaded file must contain the following columns: {', '.join(required_columns)}"
        )
    else:
        st.subheader("Processing Results")

        # Create feedback pipeline
        standalone_provider = CustomFeedBackFunction()
        f_custom_function = Feedback(standalone_provider.custom_metric_score).on(
            question=Select.RecordInput,
            context=Select.RecordInput,
            answer=Select.RecordOutput,
        )

        # Process each row in the uploaded data
        results = []
        for index, row in data.iterrows():
            # Simulate session context
            with TruSession() as session:
                # Record the input data
                record = {
                    "question": row["Question"],
                    "context": row["Context"],
                    "answer": row["Answer"]
                }
                feedback_results = session.run_feedback_functions(
                    record=record,
                    feedback_functions=[f_custom_function]
                )

                # Extract score and explanation from results
                result = feedback_results[0]
                results.append({
                    "Row": index + 1,
                    "Score": result.result,
                    "Reason": result.calls[0].meta.get("reason", "No explanation provided")
                })

        # Show results to user
        st.write("### Feedback Results")
        for result in results:
            st.markdown(f"#### Row {result['Row']}")
            st.write(f"**Score:** {result['Score']}")
            st.write(f"**Reason:** {result['Reason']}")
            st.divider()

        # Allow user to download results as CSV
        download_df = pd.DataFrame(results)
        csv = download_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Results",
            data=csv,
            file_name="evaluation_results.csv",
            mime="text/csv"
        )
else:
    st.info("Please upload an Excel file to proceed.")
