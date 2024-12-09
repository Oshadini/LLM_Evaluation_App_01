import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.feedback import prompts
from trulens_eval import Feedback, Select, Tru


# Load Trulens feedback class (customized scoring metrics)
class CustomFeedback(OpenAI):
    """
    Custom feedback class extends OpenAI's scoring logic.
    This is needed to evaluate answers/contexts/questions using Trulens feedback.
    """
    def custom_metric_score(self, answer=None, question=None, context=None):
        """
        Calculate a custom metric score for evaluation.
        """
        if answer and question and context:
            # Evaluate context + question relevance
            user_prompt = f"Answer: {answer}\nQuestion: {question}\nContext: {context}\n"
            result = self.generate_score_and_reasons(prompts.COT_REASONS_TEMPLATE, user_prompt)
            return result
        return 0.0, {}


# Instantiate feedback mechanism
feedback_provider = CustomFeedback()


# Streamlit App for the main UI
st.set_page_config(
    page_title="Trulens Evaluation UI",
    page_icon="✅",
    layout="wide"
)

st.title("Trulens Evaluation - Excel Input Workflow")

st.markdown("""
Upload an Excel file with `Context`, `Question`, and `Answer`. 
This will allow Trulens to evaluate them via a custom chain.
""")

# Excel File Upload Section
uploaded_file = st.file_uploader("Upload your Excel file with columns (Context, Question, Answer):", type=["xlsx", "csv"])

if uploaded_file:
    # Load the uploaded data into a DataFrame
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)

    # Ensure the required columns exist
    if {"Context", "Question", "Answer"}.issubset(df.columns):
        st.success("Columns detected: Context, Question, Answer")
        st.write(df)

        # Loop through each input pair
        st.subheader("Evaluating Trulens Feedback Chain...")
        with st.spinner("Evaluating using Trulens..."):
            results = []
            for index, row in df.iterrows():
                # Wrap string values into Trulens Select Lens
                context = Select.RecordInput(row['Context'])
                question = Select.RecordInput(row['Question'])
                answer = Select.RecordOutput(row['Answer'])

                # Feedback chain setup
                f_feedback = Feedback(feedback_provider.custom_metric_score).on(
                    answer=answer,
                    question=question,
                    context=context
                )

                # Run Trulens evaluation
                tru = Tru()
                with tru as chain:
                    chain.invoke()
                    feedback_result = tru.get_records_and_feedback()
                
                # Display results
                st.write(f"Row {index + 1}")
                st.write(f"Answer: {row['Answer']}")
                st.write(f"Context: {row['Context']}")
                st.write(f"Feedback Results: {feedback_result}")
    else:
        st.error("The uploaded Excel file must contain the columns: Context, Question, and Answer")
else:
    st.info("Please upload an Excel file to start the evaluation workflow.")
