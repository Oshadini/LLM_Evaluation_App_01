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

            # Initialize session state to store system prompts and results
            if "system_prompts" not in st.session_state:
                st.session_state.system_prompts = {}
            if "combined_results" not in st.session_state:
                st.session_state.combined_results = []

            for i in range(num_metrics):
                st.markdown(f"### Metric {i + 1}")

                selected_columns = st.multiselect(
                    f"Select columns for Metric {i + 1}:",
                    options=required_columns[1:],
                    key=f"columns_{i}"
                )

                toggle_prompt = st.checkbox(
                    f"Automatically generate system prompt for Metric {i + 1}?", key=f"toggle_prompt_{i}"
                )

                if toggle_prompt:
                    if len(selected_columns) < 1:
                        st.error(f"For Metric {i + 1}, please select at least one column.")
                    else:
                        if f"metric_{i}" not in st.session_state.system_prompts:
                            try:
                                selected_column_names = ", ".join(selected_columns)
                                completion = openai.chat.completions.create(
                                    model="gpt-4",  # Correct model name
                                    messages=[ 
                                        {"role": "system", "content": "You are a helpful assistant generating system prompts."},
                                        {"role": "user", "content": f"Generate a system prompt less than 200 tokens to evaluate relevance based on the following columns: {selected_column_names}."}
                                    ],
                                    max_tokens=200
                                )
                                system_prompt = completion.choices[0].message.content.strip()
                                st.session_state.system_prompts[f"metric_{i}"] = system_prompt
                            except Exception as e:
                                st.error(f"Error generating or processing system prompt: {e}")

                        system_prompt = st.session_state.system_prompts.get(f"metric_{i}", "")
                        st.text_area(
                            f"Generated System Prompt for Metric {i + 1}:", value=system_prompt, height=200
                        )
                        st.success(f"System Prompt for Metric {i + 1} is valid.")
                else:
                    system_prompt = st.text_area(
                        f"Enter the System Prompt for Metric {i + 1}:",
                        height=200
                    )

                    valid_prompt = st.button(f"Validate Prompt for Metric {i + 1}", key=f"validate_{i}")

                    if valid_prompt:
                        selected_column_terms = {
                            col.lower().replace(" ", "_"): col
                            for col in selected_columns
                        }
                        errors = []
                        for term, original_column in selected_column_terms.items():
                            term_pattern = f"\\b{term.replace('_', ' ')}\\b"
                            if not re.search(term_pattern, system_prompt, re.IGNORECASE):
                                errors.append(f"'{original_column}' needs to be included as '{term.replace('_', ' ')}' in the system prompt.")

                        if errors:
                            st.error(
                                f"For Metric {i + 1}, the following errors were found in your system prompt: "
                                f"{'; '.join(errors)}"
                            )
                        else:
                            st.success(f"System Prompt for Metric {i + 1} is valid.")

                # Button for generating results for each metric
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
                    st.session_state.combined_results.extend(results)
                    st.write(f"Results for Metric {i + 1}:")
                    st.dataframe(pd.DataFrame(results))

            # Button for generating combined results - only show if more than one metric is selected
            if num_metrics > 1 and st.button("Generate Combined Results"):
                if st.session_state.combined_results:
                    st.write("Combined Results:")
                    st.dataframe(pd.DataFrame(st.session_state.combined_results))
                else:
                    st.warning("No results to combine. Please generate results for individual metrics first.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
