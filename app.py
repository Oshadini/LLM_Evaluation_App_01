import streamlit as st
import pandas as pd
import re
from typing import Tuple, Dict
from trulens.core import Feedback
from trulens.providers.openai import OpenAI as fOpenAI
from trulens.core import TruSession
from trulens.feedback import prompts
import openai

# Initialize the session
session = TruSession()

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define the custom class
class prompt_with_conversation_relevence(fOpenAI):
    def prompt_with_conversation_relevence_feedback(self, **kwargs) -> Tuple[float, Dict]:
        """
        Process the dynamically selected parameters to generate relevance feedback.
        """
        user_prompt = ""
        if "question" in kwargs:
            user_prompt += "question: {question}\n\n"
        if "formatted_history" in kwargs:
            user_prompt += "answer: {formatted_history}\n\n"
        if "formatted_reference_content" in kwargs:
            user_prompt += "reference_content: {formatted_reference_content}\n\n"
        if "formatted_reference_answer" in kwargs:
            user_prompt += "reference_answer: {formatted_reference_answer}\n\n"
        if "formatted_content" in kwargs:
            user_prompt += "content: {formatted_content}\n\n"
        user_prompt += "RELEVANCE: "

        user_prompt = user_prompt.format(**kwargs)

        user_prompt = user_prompt.replace(
            "RELEVANCE:", prompts.COT_REASONS_TEMPLATE
        )

        result = self.generate_score_and_reasons(kwargs["system_prompt"], user_prompt)

        details = result[1]
        reason = details['reason'].split('\n')
        criteria = reason[0].split(': ')[1]
        supporting_evidence = reason[1].split(': ')[1]
        score = reason[-1].split(': ')[1]

        return score, {"criteria": criteria, "supporting_evidence": supporting_evidence}

# Initialize the custom class
prompt_with_conversation_relevence_custom = prompt_with_conversation_relevence()

# Streamlit UI
st.title("LLM Evaluation Tool")
st.write("Upload an Excel file with columns: Index, Question, Content, Answer, Reference Content, Reference Answer to evaluate relevance scores.")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        required_columns = ["Index", "Question", "Content", "Answer", "Reference Content", "Reference Answer"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"The uploaded file must contain these columns: {', '.join(required_columns)}.")
        else:
            st.write("Preview of Uploaded Data:")
            st.dataframe(df.head())

            num_metrics = st.number_input("Enter the number of metrics you want to define:", min_value=1, step=1)

            all_results = []
            for i in range(num_metrics):
                st.markdown(f"### Metric {i + 1}")

                selected_columns = st.multiselect(
                    f"Select columns for Metric {i + 1}:",
                    options=required_columns[1:],
                    key=f"columns_{i}"
                )

                system_prompt = st.text_area(
                    f"Enter the System Prompt for Metric {i + 1}:",
                    height=200
                )

                if st.button(f"Generate Results for Metric {i + 1}", key=f"generate_results_{i}"):
                    column_mapping = {
                        "Question": "question",
                        "Content": "formatted_content",
                        "Answer": "formatted_history",
                        "Reference Content": "formatted_reference_content",
                        "Reference Answer": "formatted_reference_answer"
                    }
                    results = []
                    for index, row in df.iterrows():
                        params = {"system_prompt": system_prompt}
                        for col in selected_columns:
                            if col in column_mapping:
                                params[column_mapping[col]] = row[col]

                        score, details = prompt_with_conversation_relevence_custom.prompt_with_conversation_relevence_feedback(**params)
                        result_row = {
                            "Index": row["Index"],
                            "Metric": f"Metric {i + 1}",
                            "Score": score,
                            "Criteria": details["criteria"],
                            "Supporting Evidence": details["supporting_evidence"]
                        }
                        results.append(result_row)

                    metric_results = pd.DataFrame(results)
                    st.write(f"Results for Metric {i + 1}:")
                    st.dataframe(metric_results)
                    all_results.append(metric_results)

            if all_results and st.button("Generate Concatenated Results Table"):
                concatenated_results = pd.concat(all_results, ignore_index=True)
                st.write("Concatenated Results Table:")
                st.dataframe(concatenated_results)

    except Exception as e:
        st.error(f"An error occurred: {e}")
