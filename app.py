import streamlit as st
import pandas as pd
from typing import Optional, Dict, Tuple
from trulens_eval.feedback.provider import OpenAI
from langchain_openai import ChatOpenAI
from trulens_eval import Feedback, Select, Tru, TruChain

# Extend OpenAI provider with custom feedback functions
class Custom_FeedBack(OpenAI):
    def style_check_professional(self, response: str) -> float:
        """
        Custom feedback function to grade the professional style of the response.

        Args:
            response (str): Text to be graded for professional style.

        Returns:
            float: A value between 0 and 1. 0 being "not professional" and 1 being "professional".
        """
        professional_prompt = f"""
        Please rate the professionalism of the following text on a scale from 0 to 10, where 0 is not at all professional and 10 is extremely professional:

        {response}
        """
        return self.generate_score(system_prompt=professional_prompt)

class CustomOpenAIReasoning(OpenAI):
    def context_relevance_with_cot_reasons_extreme(self, question: str, context: str) -> Tuple[float, Dict]:
        """
        Tweaked version of context relevance with chain-of-thought (CoT) reasoning, extending OpenAI provider.

        Args:
            question (str): The question being asked.
            context (str): A statement to the question.

        Returns:
            Tuple[float, Dict]: Score between 0-1 and reasoning explanation.
        """
        system_prompt = "RELEVANCE"
        user_prompt = f"""
        Evaluate the relevance of the following context to the question, providing reasons using a chain-of-thought methodology:

        Question: {question}
        Context: {context}
        """
        return self.generate_score_and_reasons(system_prompt=system_prompt, user_prompt=user_prompt)

# Function to manage feedback evaluation
def manage_feedback(row_data: Dict[str, str], feedback: Feedback):
    """
    Evaluate feedback for the given row data and feedback function.

    Args:
        row_data (Dict[str, str]): A dictionary of row data.
        feedback (Feedback): Feedback function to evaluate.

    Returns:
        Dict: Feedback evaluation results including score and reasoning.
    """
    # Ensure proper initialization of ChatOpenAI and wrapping in a chain
    app = ChatOpenAI(model="gpt-4o", openai_api_key=st.secrets["OPENAI_API_KEY"], max_tokens=1024)

    # Combine all selected columns into a single prompt
    prompt = "\n".join([f"{key}: {value}" for key, value in row_data.items() if value])

    # Wrap ChatOpenAI in TruChain for proper recording
    tru_recorder = TruChain(chain=app.invoke, app_id='C', feedbacks=[feedback])

    with tru_recorder as recording:
        # Invoke the prompt and record it
        llm_response = app.invoke(prompt)

    # Fetch recording data
    rec = recording.get()

    feedback_results = {}
    feedback_data = rec.wait_for_feedback_results()

    if not feedback_data:
        return {"error": "No feedback results were generated. Ensure the feedback logic is correct."}

    for feedback_obj, feedback_result in feedback_data.items():
        # Safeguard: Check if 'calls' exist and are non-empty
        if not feedback_result.calls:
            feedback_results[feedback_obj.name] = {
                "score": None,
                "reason": "No calls were recorded. Check your chain/app setup."
            }
            continue

        meta = feedback_result.calls[0].meta
        feedback_results[feedback_obj.name] = {
            "score": feedback_result.result,
            "reason": meta.get("reason", "No reason provided")
        }

    return feedback_results




# Streamlit App Configuration
st.set_page_config(
    page_title="Custom Metrics Evaluation",
    page_icon="📊",
    layout="wide"
)
st.title("Custom Metrics Evaluation Using TruLens")

# File Upload
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    # Load and display the Excel file
    data = pd.read_excel(uploaded_file)
    st.write("File Loaded:")
    st.dataframe(data)

    # User input for number of metrics
    num_metrics = st.number_input("How many metrics do you want to define?", min_value=1, max_value=10, step=1)

    feedback_functions = []
    metric_tabs = st.tabs([f"Metric {i+1}" for i in range(num_metrics)])

    for i, tab in enumerate(metric_tabs):
        with tab:
            st.subheader(f"Define Metric {i+1}")
            metric_name = st.text_input(f"Metric Name for Metric {i+1}")
            columns = st.multiselect(f"Select input combinations for Metric {i+1}", options=data.columns)
            feedback_type = st.selectbox(f"Feedback Type for Metric {i+1}", ["Professional Style", "Context Relevance"])

            if feedback_type == "Professional Style":
                custom_feedback_provider = Custom_FeedBack()
                feedback = Feedback(custom_feedback_provider.style_check_professional)
            elif feedback_type == "Context Relevance":
                custom_feedback_provider = CustomOpenAIReasoning()
                feedback = Feedback(custom_feedback_provider.context_relevance_with_cot_reasons_extreme)

            feedback_functions.append((metric_name, feedback, columns))

    if st.button("Evaluate Metrics"):
        st.subheader("Evaluation Results")
        for index, row in data.iterrows():
            st.markdown(f"### Row {index + 1} Results")

            row_data = row.to_dict()
            for metric_name, feedback_function, selected_columns in feedback_functions:
                selected_data = {col: row_data[col] for col in selected_columns if col in row_data}
                results = manage_feedback(selected_data, feedback_function)

                for feedback_name, result in results.items():
                    st.write(f"**Metric:** {feedback_name}")
                    st.write(f"**Score:** {result['score']}")
                    st.write(f"**Reason:** {result['reason']}")
                    st.divider()
else:
    st.info("Please upload an Excel file to proceed.")
