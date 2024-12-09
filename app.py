import streamlit as st
import pandas as pd
import json
from typing import Optional, Dict, Tuple
from trulens_eval.feedback.provider import OpenAI
from langchain_openai import ChatOpenAI
from typing import Dict, Tuple
from trulens.feedback import prompts


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


# Streamlit App Configuration
st.set_page_config(
    page_title="Custom Metrics Evaluation",
    page_icon="📊",
    layout="wide"
)
st.title("Custom Metrics Evaluation Using TruLens")


# File Upload
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

# Placeholder model for generating responses
model = ChatOpenAI(model="gpt-4o", openai_api_key=st.secrets["OPENAI_API_KEY"], max_tokens=1024)


# Feedback Class
class CustomFeedback:
    def __init__(self):
        self.feedbacks = []

    def add_feedback(self, metric_name, feedback_function, combination):
        self.feedbacks.append({"metric_name": metric_name, "feedback_function": feedback_function, "combination": combination})

    def evaluate(self, data_row):
        results = []
        for feedback in self.feedbacks:
            feedback_function = feedback["feedback_function"]
            combination = feedback["combination"]

            # Generate input text for the feedback function
            try:
                input_text = "\n".join([f"{col}: {data_row[col]}" for col in combination if col in data_row])
                # Invoke feedback function
                result = feedback_function(input_text)
                
                # Handle reasoning for results if available
                explanation = "Processed successfully" if isinstance(result, float) else "Invalid result type"
                if isinstance(result, tuple):  # Assuming reasoning tuple
                    explanation = result[1].get("reason", "No reason provided")
                    result_score = result[0]
                else:
                    result_score = result
                    explanation = "Processed successfully"
                
                results.append({
                    "metric": feedback["metric_name"],
                    "score": result_score,
                    "explanation": explanation,
                })
            except Exception as e:
                results.append({
                    "metric": feedback["metric_name"],
                    "score": "Error",
                    "explanation": str(e),
                })
        return results


if uploaded_file:
    # Load and display the Excel file
    data = pd.read_excel(uploaded_file)
    st.write("File Loaded:")
    st.dataframe(data)

    # User input for number of metrics
    num_metrics = st.number_input("How many metrics do you want to define?", min_value=1, max_value=10, step=1)

    feedback = CustomFeedback()
    metric_tabs = st.tabs([f"Metric {i+1}" for i in range(num_metrics)])

    for i, tab in enumerate(metric_tabs):
        with tab:
            st.subheader(f"Define Metric {i+1}")
            metric_name = st.text_input(f"Metric Name for Metric {i+1}")
            columns = st.multiselect(f"Select input combinations for Metric {i+1}", options=data.columns)
            feedback_type = st.selectbox(f"Feedback Type for Metric {i+1}", ["Professional Style", "Context Relevance"])

            if feedback_type == "Professional Style":
                custom_feedback_provider = Custom_FeedBack()
                feedback.add_feedback(metric_name, custom_feedback_provider.style_check_professional, columns)
            elif feedback_type == "Context Relevance":
                custom_feedback_provider = CustomOpenAIReasoning()
                feedback.add_feedback(metric_name, custom_feedback_provider.context_relevance_with_cot_reasons_extreme, columns)

    if st.button("Evaluate Metrics"):
        st.subheader("Evaluation Results")
        for index, row in data.iterrows():
            results = feedback.evaluate(row.to_dict())
            st.markdown(f"### Row {index + 1} Results")
            for result in results:
                st.write(f"**Metric:** {result['metric']}")
                st.write(f"**Score:** {result['score']}")
                st.write(f"**Reason/Explanation:** {result['explanation']}")
                st.divider()
else:
    st.info("Please upload an Excel file to proceed.")
