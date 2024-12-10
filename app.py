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
        system_prompt = """You are a RELEVANCE grader; providing the relevance of the given CHAT_GUIDANCE to the given CHAT_CONVERSATION.
            Respond only as a number from 0 to 10 where 0 is the least relevant and 10 is the most relevant. 

            A few additional scoring guidelines:
            - Long CHAT_CONVERSATION should score equally well as short CHAT_CONVERSATION.
            - RELEVANCE score should increase as the CHAT_CONVERSATION provides more RELEVANT context to the CHAT_GUIDANCE.
            - RELEVANCE score should increase as the CHAT_CONVERSATION provides RELEVANT context to more parts of the CHAT_GUIDANCE.
            - CHAT_CONVERSATION that is RELEVANT to some of the CHAT_GUIDANCE should score of 2, 3 or 4. Higher score indicates more RELEVANCE.
            - CHAT_CONVERSATION that is RELEVANT to most of the CHAT_GUIDANCE should get a score of 5, 6, 7 or 8. Higher score indicates more RELEVANCE.
            - CHAT_CONVERSATION that is RELEVANT to the entire CHAT_GUIDANCE should get a score of 9 or 10. Higher score indicates more RELEVANCE.
            - CHAT_CONVERSATION must be relevant and helpful for answering the entire CHAT_GUIDANCE to get a score of 10.
            - Never elaborate."""

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
                st.write(details)
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
