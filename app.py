# app.py
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
    def prompt_with_conversation_relevence_feedback(self, question: str, formatted_history: str) -> Tuple[float, Dict]:
        """
        Process the question and formatted history to generate relevance feedback.
        """
        # Get the system_prompt as user input
        st.write("Enter the system prompt below:")
        system_prompt = st.text_area(
            "System Prompt",
            placeholder="Enter the system prompt to guide the relevance evaluation...",
            height=200
        )
        if not system_prompt.strip():
            st.error("System prompt cannot be empty. Please enter a valid prompt.")
            return None, {"criteria": "N/A", "supporting_evidence": "N/A"}

        # Construct the user prompt
        user_prompt = """CHAT_GUIDANCE: {question}

        CHAT_CONVERSATION: {formatted_history}
        
        RELEVANCE: """
        user_prompt = user_prompt.format(question=question, formatted_history=formatted_history)

        # Replace RELEVANCE with additional reasoning templates
        user_prompt = user_prompt.replace(
            "RELEVANCE:", prompts.COT_REASONS_TEMPLATE
        )

        # Generate results
        result = self.generate_score_and_reasons(system_prompt, user_prompt)

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
st.write("Upload an Excel file with columns: `question` and `answer` to evaluate relevance scores.")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
if uploaded_file:
    try:
        # Load the Excel file
        df = pd.read_excel(uploaded_file)

        # Validate required columns
        if not all(col in df.columns for col in ["question", "answer"]):
            st.error("The uploaded file must contain `question` and `answer` columns.")
        else:
            st.write("Preview of Uploaded Data:")
            st.dataframe(df.head())

            # Process each row
            results = []
            for index, row in df.iterrows():
                # Extract question and formatted history from the file
                question = row["question"]
                formatted_history = row["answer"]

                # Generate relevance feedback
                score, details = prompt_with_conversation_relevence_custom.prompt_with_conversation_relevence_feedback(
                    question, formatted_history
                )
                if score is None:  # Skip processing if the system prompt was invalid
                    continue
                results.append({
                    "question": question,
                    "formatted_history": formatted_history,
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
    except Exception as e:
        st.error(f"An error occurred: {e}")
