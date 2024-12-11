# Updated Code with Automatic System Prompt Toggle
import streamlit as st
import pandas as pd
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

            metric_definitions = []
            colors = ["#FFCCCC", "#CCE5FF", "#D5F5E3", "#F9E79F", "#FAD7A0"]  # Background colors for metrics
            
            for i in range(num_metrics):
                bg_color = colors[i % len(colors)]
                st.markdown(
                    f"""
                    <div style="background-color: {bg_color}; padding: 15px; margin-bottom: 15px; border-radius: 5px;">
                    <h4 style="margin-top: 0;">Metric {i + 1}</h4>
                    """,
                    unsafe_allow_html=True,
                )

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
                        try:
                            selected_column_names = ", ".join(selected_columns)
                            completion = openai.chat.completions.create(
                                model="gpt-4o",
                                prompt=f"Generate a system prompt to evaluate relevance based on the following columns: {selected_column_names}",
                                max_tokens=200
                            )
                            auto_generated_prompt = completion.choices[0].text.strip()
                            st.text_area(
                                f"Generated System Prompt for Metric {i + 1}:", value=auto_generated_prompt, height=200
                            )
                        except Exception as e:
                            st.error(f"Error generating system prompt: {e}")
                else:
                    system_prompt = st.text_area(
                        f"Enter the System Prompt for Metric {i + 1}:",
                        height=200
                    )

                valid_prompt = st.button(f"Validate Prompt for Metric {i + 1}", key=f"validate_{i}")

                if len(selected_columns) < 1:
                    st.error(f"For Metric {i + 1}, you must select at least one column.")
                    continue

                if valid_prompt and not toggle_prompt:
                    selected_column_terms = {
                        col.lower().replace(" ", "_"): col
                        for col in selected_columns
                    }
                    errors = []
                    for term, original_column in selected_column_terms.items():
                        if term not in system_prompt.lower():
                            errors.append(f"'{original_column}' needs to be included as '{term.replace('_', ' ')}' in the system prompt.")

                    if errors:
                        st.error(
                            f"For Metric {i + 1}, the following errors were found in your system prompt: "
                            f"{'; '.join(errors)}"
                        )
                        continue
                    else:
                        st.success(f"System Prompt for Metric {i + 1} is valid.")

                metric_definitions.append({
                    "system_prompt": auto_generated_prompt if toggle_prompt else system_prompt,
                    "selected_columns": selected_columns
                })

                st.markdown("</div>", unsafe_allow_html=True)

            if st.button("Generate Results"):
                if not metric_definitions:
                    st.error("Please define at least one metric with a valid system prompt and selected columns.")
                else:
                    column_mapping = {
                        "Question": "question",
                        "Content": "formatted_content",
                        "Answer": "formatted_history",
                        "Reference Content": "formatted_reference_content",
                        "Reference Answer": "formatted_reference_answer"
                    }

                    results = []
                    for metric_index, metric in enumerate(metric_definitions, start=1):
                        system_prompt = metric["system_prompt"]
                        selected_columns = metric["selected_columns"]

                        for index, row in df.iterrows():
                            params = {"system_prompt": system_prompt}
                            for col in selected_columns:
                                if col in column_mapping:
                                    params[column_mapping[col]] = row[col]

                            score, details = prompt_with_conversation_relevence_custom.prompt_with_conversation_relevence_feedback(**params)

                            result_row = {
                                "Index": row["Index"],  # Maintain Index column
                                "Metric": f"Metric {metric_index}",
                                "Selected Columns": ", ".join(selected_columns),
                                "Score": score,
                                "Criteria": details["criteria"],
                                "Supporting Evidence": details["supporting_evidence"]
                            }

                            for col in required_columns:
                                if col != "Index":
                                    result_row[col] = row[col]

                            results.append(result_row)

                    results_df = pd.DataFrame(results)
                    st.write("Results:")
                    st.dataframe(results_df)

                    st.download_button(
                        label="Download Results as CSV",
                        data=results_df.to_csv(index=False),
                        file_name="relevance_results.csv",
                        mime="text/csv",
                    )
    except Exception as e:
        st.error(f"An error occurred: {e}")
