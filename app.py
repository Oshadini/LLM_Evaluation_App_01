# Corrected Code with Updated Validation and Order
import streamlit as st
import pandas as pd
from typing import Tuple, Dict
from trulens.core import Feedback
from trulens.providers.openai import OpenAI as fOpenAI
from trulens.core import TruSession
from trulens.feedback import prompts

# Initialize the session
session = TruSession()

# Define the custom class
class prompt_with_conversation_relevence(fOpenAI):
    def prompt_with_conversation_relevence_feedback(self, **kwargs) -> Tuple[float, Dict]:
        """
        Process the dynamically selected parameters to generate relevance feedback.
        """
        # Dynamically construct the user prompt based on provided parameters and selected columns
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

        # Format the user prompt with the provided values
        user_prompt = user_prompt.format(**kwargs)

        # Replace RELEVANCE with additional reasoning templates
        user_prompt = user_prompt.replace(
            "RELEVANCE:", prompts.COT_REASONS_TEMPLATE
        )

        # Generate results
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
st.write("Upload an Excel file with columns: Question, Content, Answer, Reference Content, Reference Answer to evaluate relevance scores.")

# Step 1: File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Load the Excel file
        df = pd.read_excel(uploaded_file)

        # Validate required columns
        required_columns = ["Question", "Content", "Answer", "Reference Content", "Reference Answer"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"The uploaded file must contain these columns: {', '.join(required_columns)}.")
        else:
            st.write("Preview of Uploaded Data:")
            st.dataframe(df.head())

            # Step 2: Select number of metrics
            num_metrics = st.number_input("Enter the number of metrics you want to define:", min_value=1, step=1)

            metric_definitions = []
            for i in range(num_metrics):
                st.subheader(f"Metric {i + 1}")
                
                # Selection comes before prompt input
                selected_columns = st.multiselect(
                    f"Select columns for Metric {i + 1}:",
                    options=required_columns,
                    key=f"columns_{i}"
                )

                # Ensure at least two columns are selected
                if len(selected_columns) < 2:
                    st.error(f"For Metric {i + 1}, you must select at least two columns.")
                    continue
                
                # Prompt input comes after selection
                system_prompt = st.text_area(f"Enter the System Prompt for Metric {i + 1}:")
                valid_prompt = st.button(f"Validate Prompt for Metric {i + 1}")

                # Ensure matched_terms is always defined
                valid_terms = ["question", "answer", "content", "reference content", "reference answer"]
                matched_terms = [term for term in valid_terms if term in system_prompt.lower()]

                # Disregard "answer" if "reference answer" is in the prompt
                if "reference answer" in system_prompt.lower():
                    matched_terms = [term for term in matched_terms if term != "answer"]

                # Disregard "content" if "reference content" is in the prompt
                if "reference content" in system_prompt.lower():
                    matched_terms = [term for term in matched_terms if term != "content"]

                if valid_prompt:
                    # Validate the system prompt
                    if not system_prompt.strip():
                        st.error(f"For Metric {i + 1}, the system prompt cannot be empty.")
                        continue
                    
                    # Validate column selection alignment with system prompt
                    column_mapping = {
                        "question": "Question",
                        "answer": "Answer",
                        "content": "Content",
                        "reference content": "Reference Content",
                        "reference answer": "Reference Answer"
                    }

                    missing_terms = []
                    for term in matched_terms:
                        if column_mapping[term] not in selected_columns:
                            missing_terms.append(term)
                    
                    if missing_terms:
                        missing_columns = [column_mapping[term] for term in missing_terms]
                        st.error(
                            f"For Metric {i + 1}, the system prompt references '{', '.join(missing_terms)}', "
                            f"but you need to select these columns: {', '.join(missing_columns)}."
                        )
                        continue
                    else:
                        st.success(f"System Prompt for Metric {i + 1} is valid.")

                    metric_definitions.append({
                        "system_prompt": system_prompt,
                        "selected_columns": selected_columns
                    })

            # Step 3: Generate results
            if st.button("Generate Results"):
                if not metric_definitions:
                    st.error("Please define at least one metric with a valid system prompt and selected columns.")
                else:
                    # Map column names to variable names
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
                            # Prepare dynamic parameters based on selected columns
                            params = {"system_prompt": system_prompt}
                            for col in selected_columns:
                                if col in column_mapping:
                                    params[column_mapping[col]] = row[col]

                            # Generate score and feedback
                            score, details = prompt_with_conversation_relevence_custom.prompt_with_conversation_relevence_feedback(**params)

                            # Append results with correct metric index
                            results.append({
                                "Metric": f"Metric {metric_index}",
                                "Selected Columns": ", ".join(selected_columns),
                                "Score": score,
                                "Criteria": details["criteria"],
                                "Supporting Evidence": details["supporting_evidence"]
                            })

                    # Convert results to DataFrame
                    results_df = pd.DataFrame(results)
                    st.write("Results:")
                    st.dataframe(results_df)

                    # Download results as CSV
                    st.download_button(
                        label="Download Results as CSV",
                        data=results_df.to_csv(index=False),
                        file_name="relevance_results.csv",
                        mime="text/csv",
                    )
    except Exception as e:
        st.error(f"An error occurred: {e}")
