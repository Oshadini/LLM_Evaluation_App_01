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
        if "formatted_reference_context" in kwargs:
            user_prompt += "reference_context: {formatted_reference_context}\n\n"
        if "formatted_reference_answer" in kwargs:
            user_prompt += "reference_answer: {formatted_reference_answer}\n\n"
        if "formatted_context" in kwargs:
            user_prompt += "context: {formatted_context}\n\n"
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
st.write("Upload an Excel file for processing. The expected formats are:")
st.write("1. Columns: Index, Question, Context, Answer, Reference Context, Reference Answer")
st.write("2. Columns: Index, Conversation, Agent Prompt")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Read uploaded file
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        if "Question" in df.columns and "Context" in df.columns and "Answer" in df.columns:
            # Code 1 processing
            required_columns = ["Index", "Question", "Context", "Answer", "Reference Context", "Reference Answer"]
            if not all(col in df.columns for col in required_columns):
                st.error(f"The uploaded file must contain these columns: {', '.join(required_columns)}.")
            else:
                st.write("Preview of Uploaded Data:")
                st.dataframe(df.head())

                num_metrics = st.number_input("Enter the number of metrics you want to define:", min_value=1, step=1)

                if "system_prompts" not in st.session_state:
                    st.session_state.system_prompts = {}
                if "combined_results" not in st.session_state:
                    st.session_state.combined_results = []

                for i in range(num_metrics):
                    st.markdown(f"""
                        <hr style="border: 5px solid #000000;">
                        <h3 style="background-color: #f0f0f0; padding: 10px; border: 2px solid #000000;">
                            Metric {i + 1}
                        </h3>
                    """, unsafe_allow_html=True)

                    selected_columns = st.multiselect(
                        f"Select columns for Metric {i + 1}:",
                        options=required_columns[1:],
                        key=f"columns_{i}"
                    )

                    toggle_prompt = st.checkbox(
                        f"Automatically generate system prompt for Metric {i + 1}", key=f"toggle_prompt_{i}"
                    )

                    if toggle_prompt:
                        if len(selected_columns) < 1:
                            st.error(f"For Metric {i + 1}, please select at least one column.")
                        else:
                            if f"metric_{i}" not in st.session_state.system_prompts:
                                try:
                                    selected_column_names = ", ".join(selected_columns)

                                    evaluation_type = "Factual Correctness" if (i + 1) % 2 == 0 else "Relevance"

                                    completion = openai.chat.completions.create(
                                        model="gpt-4o",
                                        messages=[
                                            {"role": "user", "content": (
                                                f"Generate a system prompt less than 200 tokens to evaluate {evaluation_type.lower()} "
                                                f"based on the following columns: {selected_column_names}. "
                                                f"Please provide a rating from 1 (not at all {evaluation_type.lower()}) to 10 (highly {evaluation_type.lower()})."
                                            )}
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

                        valid_prompt = st.button(f"Validate Metric {i + 1}", key=f"validate_{i}")

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

                    if st.button(f"Metric {i + 1} Results", key=f"generate_results_{i}"):
                        column_mapping = {
                            "Question": "question",
                            "Context": "formatted_context",
                            "Answer": "formatted_history",
                            "Reference Context": "formatted_reference_context",
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
                                "Selected Columns": ", ".join(selected_columns),
                                "Score": score,
                                "Criteria": details["criteria"],
                                "Supporting Evidence": details["supporting_evidence"],
                                "Question": row["Question"],
                                "Context": row["Context"],
                                "Answer": row["Answer"],
                                "Reference Context": row["Reference Context"],
                                "Reference Answer": row["Reference Answer"]
                            }
                            results.append(result_row)
                        st.session_state.combined_results.extend(results)
                        st.write(f"Results for Metric {i + 1}:")
                        st.dataframe(pd.DataFrame(results))

                if num_metrics > 1 and st.button("Overall Results"):
                    if st.session_state.combined_results:
                        st.write("Combined Results:")
                        st.dataframe(pd.DataFrame(st.session_state.combined_results))
                    else:
                        st.warning("No results to combine. Please generate results for individual metrics first.")

        elif "Conversation" in df.columns and "Agent Prompt" in df.columns:
            # Code 2 processing
            required_columns = ["Index", "Conversation", "Agent Prompt"]
            if not all(col in df.columns for col in required_columns):
                st.error(f"The uploaded file must contain these columns: {', '.join(required_columns)}.")
            else:
                st.write("Preview of Uploaded Data:")
                st.dataframe(df.head())

                num_metrics = st.number_input("Enter the number of metrics you want to define:", min_value=1, step=1)

                if "system_prompts" not in st.session_state:
                    st.session_state.system_prompts = {}
                if "combined_results" not in st.session_state:
                    st.session_state.combined_results = []

                for i in range(num_metrics):
                    st.markdown(f"""
                        <hr style="border: 5px solid #000000;">
                        <h3 style="background-color: #f0f0f0; padding: 10px; border: 2px solid #000000;">
                            Metric {i + 1}
                        </h3>
                    """, unsafe_allow_html=True)

                    selected_columns = st.multiselect(
                        f"Select columns for Metric {i + 1}:",
                        options=required_columns[1:],
                        key=f"columns_{i}"
                    )

                    system_prompt = st.text_area(
                        f"Enter the System Prompt for Metric {i + 1}:",
                        height=200
                    )

                    if st.button(f"Metric {i + 1} Results", key=f"generate_results_{i}"):
                        if system_prompt.strip() == "":
                            st.error("Please enter a valid system prompt.")
                        else:
                            st.write("Evaluating conversations. Please wait...")

                            results = []
                            for index, row in df.iterrows():
                                try:
                                    evaluation_prompt = f"""
                                    System Prompt: {system_prompt}

                                    Index: {row['Index']}
                                    Conversation: {row['Conversation']}
                                    Agent Prompt: {row['Agent Prompt']}

                                    Evaluate the entire conversation for Agent-Goal Accuracy. Use the following format:
                                    
                                    Criteria: [Explain how well the Agent responded to the User's input and fulfilled their goals]
                                    Supporting Evidence: [Highlight specific faulty or insufficient responses from the Agent]
                                    Score: [Provide a numerical or qualitative score here]
                                    """

                                    completion = openai.chat.completions.create(
                                        model="gpt-4o",
                                        messages=[
                                            {"role": "system", "content": "You are an evaluator analyzing agent conversations."},
                                            {"role": "user", "content": evaluation_prompt}
                                        ]
                                    )

                                    response_content = completion.choices[0].message.content.strip()

                                    parsed_response = {
                                        "Index": row["Index"],
                                        "Metric": f"Metric {i + 1}",
                                        "Selected Columns": ", ".join(selected_columns),
                                        "Score": "",
                                        "Criteria": "",
                                        "Supporting Evidence": "",
                                        "Agent Prompt": row.get("Agent Prompt", ""),
                                        "Conversation": row.get("Conversation", "")
                                    }

                                    response_parts = response_content.split("\n")
                                    for part in response_parts:
                                        if part.startswith("Criteria:"):
                                            parsed_response["Criteria"] = part.split("Criteria:", 1)[-1].strip()
                                        elif part.startswith("Supporting Evidence:"):
                                            parsed_response["Supporting Evidence"] = part.split("Supporting Evidence:", 1)[-1].strip()
                                        elif part.startswith("Score:"):
                                            parsed_response["Score"] = part.split("Score:", 1)[-1].strip()

                                    results.append(parsed_response)
                                except Exception as e:
                                    st.error(f"Error evaluating row {index + 1}: {e}")

                            st.session_state.combined_results.extend(results)
                            st.write(f"Results for Metric {i + 1}:")
                            st.dataframe(pd.DataFrame(results))

                if num_metrics > 1 and st.button("Overall Results"):
                    if st.session_state.combined_results:
                        st.write("Combined Results:")
                        st.dataframe(pd.DataFrame(st.session_state.combined_results))
                    else:
                        st.warning("No results to combine. Please generate results for individual metrics first.")

        else:
            st.error("The uploaded file format is not recognized. Please ensure it matches one of the expected formats.")

    except Exception as e:
        st.error(f"Error processing the uploaded file: {e}")
