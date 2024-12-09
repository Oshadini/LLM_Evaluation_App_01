# File path: app.py

import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.feedback import Feedback
from trulens_eval.app import Tru, TruChain
from trulens_eval.feedback.prompts import COT_REASONS_TEMPLATE
from trulens_eval.feedback.utils import Select
from typing import Optional, Dict, Tuple

# Custom Feedback class
class Custom_FeedBack(OpenAI):
    def custom_metric_score(self, answer: Optional[str] = None, question: Optional[str] = None, context: Optional[str] = None) -> Tuple[float, Dict]:
        """
        Custom metric score function using OpenAI and Trulens.
        """
        prompt = (
            "Rate the relevance between the provided inputs on a scale of 0 to 10, "
            "where 0 is 'not at all relevant' and 10 is 'extremely relevant'. "
            "Provide a detailed explanation for the rating.\n\n"
        )

        # Generate the custom prompt based on available inputs
        if answer and question and context:
            user_prompt = f"Answer: {answer}\nQuestion: {question}\nContext: {context}\n{COT_REASONS_TEMPLATE}"
        elif answer and question:
            user_prompt = f"Answer: {answer}\nQuestion: {question}\n{COT_REASONS_TEMPLATE}"
        elif question and context:
            user_prompt = f"Question: {question}\nContext: {context}\n{COT_REASONS_TEMPLATE}"
        elif answer:
            user_prompt = f"Answer: {answer}\n{COT_REASONS_TEMPLATE}"
        elif question:
            user_prompt = f"Question: {question}\n{COT_REASONS_TEMPLATE}"
        elif context:
            user_prompt = f"Context: {context}\n{COT_REASONS_TEMPLATE}"
        else:
            user_prompt = "No inputs provided.\n" + COT_REASONS_TEMPLATE

        # Execute the feedback mechanism
        return self.generate_score_and_reasons(prompt, user_prompt)


# Initialize Custom Feedback
standalone_feedback = Custom_FeedBack()

def process_custom_metrics(data: pd.DataFrame, metrics: Dict[str, Dict]) -> pd.DataFrame:
    """
    Process the custom metrics and generate scores and explanations.
    """
    results = []
    for metric_name, metric_info in metrics.items():
        # Use Trulens Feedback mechanism
        score, reasons = standalone_feedback.custom_metric_score(
            answer=None,  # Adjust based on the desired input
            question=metric_info['prompt'],
            context=" | ".join(data[metric_info['columns']].astype(str).values.flatten())
        )

        # Append results
        results.append({
            "Metric": metric_name,
            "Selected Columns": ", ".join(metric_info["columns"]),
            "Score": score,
            "Explanation": reasons.get('reason', 'No explanation available.')
        })

    return pd.DataFrame(results)


# Main function
def main():
    st.title("Custom Metric Analysis Application with Trulens")

    # File upload section
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
    if uploaded_file:
        data = pd.read_excel(uploaded_file)
        st.write("Preview of Uploaded File:")
        st.dataframe(data)

        # Define metrics
        st.header("Metric Selection")
        num_metrics = st.number_input("Enter the number of metrics you want to define:", min_value=1, step=1, value=1)

        metrics = {}
        columns = list(data.columns)

        for i in range(1, num_metrics + 1):
            st.subheader(f"Metric {i}")
            selected_columns = st.multiselect(
                f"Select columns for Metric {i} (You can select multiple):",
                options=columns,
                key=f"metric_{i}_columns"
            )
            metric_prompt = st.text_input(
                f"Enter prompt for Metric {i}:",
                key=f"metric_{i}_prompt"
            )
            if selected_columns and metric_prompt:
                metrics[f"Metric {i}"] = {
                    "columns": selected_columns,
                    "prompt": metric_prompt
                }

        st.subheader("Selected Metrics:")
        st.write(metrics)

        # Generate Metric Scores
        if st.button("Generate Metric Scores"):
            st.subheader("Metric Scores and Explanations")
            results_df = process_custom_metrics(data, metrics)
            st.dataframe(results_df)


# Run the app
if __name__ == "__main__":
    main()
