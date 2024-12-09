from trulens_eval.app import App
from trulens_eval.feedback.provider import OpenAI
import streamlit as st
import pandas as pd
from typing import Dict, Any

class CustomFeedback(OpenAI):
    def custom_metric_score(self, answer: str = None, question: str = None, context: Any = None) -> tuple:
        """
        Example custom feedback scoring function.
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


# Instantiate Custom Feedback
standalone = CustomFeedback()

# Initialize App
app = App(
    name="your_module_path_here",  # Replace this with your actual module's logic
    module="your_module_path_here",
)

st.set_page_config(
    page_title="Evaluate with Custom Metrics",
    page_icon="📊",
    layout="wide",
)

st.title("Evaluate with Custom Metrics")
uploaded_file = st.file_uploader("Upload Excel with 'Question', 'Answer', and 'Context' columns", type=["xlsx"])

if uploaded_file:
    data = pd.read_excel(uploaded_file)
    st.write("Uploaded Data:")
    st.dataframe(data)

    required_columns = ["Question", "Answer", "Context"]
    if not all(col in data.columns for col in required_columns):
        st.error(f"Excel must include these columns: {', '.join(required_columns)}")
    else:
        st.subheader("Evaluations:")
        results = []

        # Loop over rows from uploaded data
        for index, row in data.iterrows():
            question = row.get("Question")
            answer = row.get("Answer")
            context = row.get("Context")
            
            # Dynamically prepare context
            # Wrap the context in a dictionary-like format expected by `select_context`
            context_dict = {"context": context}

            # Select context dynamically using the provided context
            with app.select_context(context_dict) as dynamic_context:
                # Feed dynamic context into a custom feedback chain
                f_custom_function = (
                    Feedback(standalone.custom_metric_score)
                    .on(answer=Select.RecordOutput)
                    .on(question=Select.RecordInput)
                    .on(context=dynamic_context)
                )

                # Simulate a chain feedback loop
                tru_recorder = TruChain(chain=None, feedbacks=[f_custom_function])

                with tru_recorder as recording:
                    llm_response = f"Simulated Response to Question {question}"

                # Fetch results
                record = recording.get()
                for feedback, feedback_result in record.wait_for_feedback_results().items():
                    if feedback.name == "custom_metric_score":
                        results.append({
                            "Row": index + 1,
                            "Score": feedback_result.result,
                            "Reason": feedback_result.calls[0].meta.get("reason", "No explanation provided")
                        })

        # Present results in the Streamlit app
        for result in results:
            st.markdown(f"### Row {result['Row']} Results")
            st.write(f"**Score:** {result['Score']}")
            st.write(f"**Reason:** {result['Reason']}")
            st.divider()
else:
    st.info("Upload a valid Excel file to begin.")
