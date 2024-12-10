# app.py
import streamlit as st
import pandas as pd
from typing import Tuple, Dict
from trulens.core import Feedback
from trulens.providers.openai import OpenAI as fOpenAI
from trulens.core import TruSession

# Initialize the session
session = TruSession()

# Define the custom class
class prompt_with_conversation_relevence(fOpenAI):
    def prompt_with_conversation_relevence_feedback(self, question: str, formatted_history: str) -> Tuple[float, Dict]:
        """
        Process the question and formatted history to generate relevance feedback with detailed criteria and evidence.
        """
        # Enhanced system prompt to explicitly request criteria and supporting evidence
        system_prompt = """You are a RELEVANCE grader. Your job is to evaluate the relevance of a CHAT_CONVERSATION (history) to a CHAT_GUIDANCE (query).
            Respond with:
            - A RELEVANCE SCORE (0 to 10, where 0 is least relevant and 10 is most relevant).
            - CRITERIA explaining why the CHAT_CONVERSATION is relevant or not.
            - SUPPORTING EVIDENCE based on specific points in the CHAT_CONVERSATION that make it relevant or irrelevant.

            Additional scoring guidelines:
            - Short or long CHAT_CONVERSATIONS should be scored equally if they provide the same amount of relevance.
            - Higher scores (5-10) should have clear alignment between CHAT_CONVERSATION and CHAT_GUIDANCE.
            - Use the specific language or context in CHAT_CONVERSATION to justify the score.
            """

        # Construct the user prompt
        user_prompt = """CHAT_GUIDANCE: {question}

        CHAT_CONVERSATION: {formatted_history}
        
        RELEVANCE SCORE: """
        user_prompt = user_prompt.format(question=question, formatted_history=formatted_history)

        # Replace RELEVANCE: with a structured response format
        user_prompt = user_prompt + """
        CRITERIA:
        SUPPORTING EVIDENCE:
        """

        # Generate results
        result = self.generate_score_and_reasons(system_prompt, user_prompt)

        # Parse the result to extract the detailed output
        details = result[1]
        reason = details['reason'].split('\n')
        score_line = [line for line in reason if line.startswith("RELEVANCE SCORE:")][0]
        criteria_line = [line for line in reason if line.startswith("CRITERIA:")][0]
        evidence_line = [line for line in reason if line.startswith("SUPPORTING EVIDENCE:")][0]

        # Extract values
        score = float(score_line.split(': ')[1])
        criteria = criteria_line.split(': ')[1]
        supporting_evidence = evidence_line.split(': ')[1]

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
