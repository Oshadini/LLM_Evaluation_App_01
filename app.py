from trulens_eval.app import App
import streamlit as st
import pandas as pd
from typing import Optional, Dict, Tuple
from trulens_eval import Feedback, Select, Tru, TruChain
from trulens_eval.feedback.provider import OpenAI


class Custom_FeedBack(OpenAI):
    def custom_metric_score(self, answer: Optional[str] = None, question: Optional[str] = None, context: Optional[any] = None) -> Tuple[float, Dict]:
        """
        A function that evaluates the relevance of an answer, question, and context.

        Args:
            answer (str): An answer being evaluated.
            question (str): A question being evaluated.
            context (str): Context for the evaluation.

        Returns:
            float: A value between 0 and 1 indicating relevance.
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

standalone = Custom_FeedBack()
st.set_page_config(
    page_title="Evaluate with Custom Metrics",
    page_icon="📊",
    layout="wide",
)
st.title("Evaluate with Custom Metrics")

# Upload an Excel file
uploaded_file = st.file_uploader("Upload an Excel file with 'Question', 'Answer', and 'Context' columns", type=["xlsx"])
if uploaded_file:
    data = pd.read_excel(uploaded_file)
    st.write("Uploaded Data:")
    st.dataframe(data)

    # Ensure required columns are present
    required_columns = ["Question", "Answer", "Context"]
    if not all(col in data.columns for col in required_columns):
        st.error(f"The uploaded file must contain the following columns: {', '.join(required_columns)}")
    else:
        st.subheader("Custom Metric Evaluation")

        # Initialize App with the required parameters
        app = App(
            root_class={
                "name": "my_custom_metric",  # Example name for identification
                "module": "your_module_path_here"  # Replace with your actual module path
            }
        )

        # Iterate over each row and evaluate
        results = []
        for index, row in data.iterrows():
            question = row.get("Question")
            answer = row.get("Answer")
            context = row.get("Context")

            # Use App.select_context() to dynamically create a Lens for context
            selected_context = app.select_context(context)  # Transform the string into a proper Lens

            # Define feedback function with the selected Lens for context
            f_custom_function = (
                Feedback(standalone.custom_metric_score)
                .on(answer=Select.RecordOutput)
                .on(question=Select.RecordInput)
                .on(context=selected_context)  # Pass the context as a Lens
            )

            # Simulate chain and record evaluation
            tru_recorder = TruChain(chain=None, feedbacks=[f_custom_function])

            with tru_recorder as recording:
                # Simulating a response
                llm_response = f"Simulated Response for Question: {question}"
                recording.record_output(llm_response)

            # Fetch feedback results
            record = recording.get()
            for feedback, feedback_result in record.wait_for_feedback_results().items():
                if feedback.name == "custom_metric_score":
                    results.append({
                        "Row": index + 1,
                        "Score": feedback_result.result,
                        "Reason": feedback_result.calls[0].meta.get("reason", "No explanation provided")
                    })

        # Display results
        for result in results:
            st.markdown(f"### Row {result['Row']} Results")
            st.write(f"**Score:** {result['Score']}")
            st.write(f"**Reason:** {result['Reason']}")
            st.divider()
else:
    st.info("Please upload an Excel file to proceed.")
