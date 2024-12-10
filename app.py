# Updated Code
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
st.title("Relevance Grader Tool")
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

            # Step 2: Let the user select columns
            selected_columns = st.multiselect(
                "Select columns to use in the prompt:",
                options=required_columns,
                default=["Question", "Answer"]
            )

            # Step 3: Input for the system prompt
            system_prompt = st.text_area("Enter the System Prompt:")

            # Check if at least one column is selected
            if selected_columns:
                # Step 4: Add a button to generate results
                if st.button("Generate Results"):
                    if system_prompt.strip() == "":
                        st.error("Please enter the system prompt.")
                    else:
                        # Map selected columns to variable names
                        column_mapping = {
                            "Question": "question",
                            "Content": "formatted_content",
                            "Answer": "formatted_history",
                            "Reference Content": "formatted_reference_content",
                            "Reference Answer": "formatted_reference_answer"
                        }

                        # Process each row
                        results = []
                        for index, row in df.iterrows():
                            # Prepare dynamic parameters based on selected columns
                            params = {"system_prompt": system_prompt}
                            for col in selected_columns:
                                if col in column_mapping:
                                    params[column_mapping[col]] = row[col]

                            # Dynamically construct criteria, supporting evidence, and score based on selected columns
                            if "Question" in selected_columns and "Answer" in selected_columns:
                                score, details = prompt_with_conversation_relevence_custom.prompt_with_conversation_relevence_feedback(**params)
                            elif "Question" in selected_columns and "Reference Answer" in selected_columns:
                                score, details = prompt_with_conversation_relevence_custom.prompt_with_conversation_relevence_feedback(**params)
                            elif "Content" in selected_columns and "Reference Content" in selected_columns:
                                score, details = prompt_with_conversation_relevence_custom.prompt_with_conversation_relevence_feedback(**params)
                            else:
                                st.error("Selected columns are not supported for relevance evaluation.")
                                continue

                            # Append results
                            st.write(details)
                            results.append({
                                "selected_columns": selected_columns,
                                "score": score,
                                "criteria": details["criteria"],
                                "supporting_evidence": details["supporting_evidence"]
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
            else:
                st.error("Please select at least one column.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
