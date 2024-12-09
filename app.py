import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.utils.generated import re_0_10_rating
from trulens_eval import Feedback, TruChain, Tru
from typing import Optional, Dict, Tuple



# Load Trulens's Feedback Class
class CustomFeedback(OpenAI):
    """
    A custom Trulens feedback function extending OpenAI's functionality for evaluation purposes.
    """
    def custom_metric_score(
        self,
        answer: Optional[str] = None,
        question: Optional[str] = None,
        context: Optional[str] = None
    ) -> Tuple[float, Dict]:
        """
        Scoring logic based on relevance.
        """
        # Generate the scoring prompt using the context, question, and answer data
        if answer and question and context:
            user_prompt = f"Prompt: Evaluate the following in terms of relevance:\nAnswer: {answer}\nQuestion: {question}\nContext: {context}\n" + prompts.COT_REASONS_TEMPLATE
        else:
            user_prompt = "Prompt: Evaluate the provided data for relevance using a scoring system:\n" + prompts.COT_REASONS_TEMPLATE

        system_prompt = prompts.CONTEXT_RELEVANCE_SYSTEM.replace(
            "- STATEMENT that is RELEVANT to most of the QUESTION should get a score of 0 - 10.",
            ""
        )

        return self.generate_score_and_reasons(system_prompt, user_prompt)





from trulens_eval.feedback import Feedback
# Instantiate Trulens Feedback
custom_feedback = CustomFeedback()

from trulens_eval.feedback.provider import OpenAI
from trulens_eval import Feedback, TruChain, Tru, Lens

def process_excel_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the uploaded data and performs Trulens evaluation on each row.
    Returns a DataFrame with results for visualization.
    """
    results = []
    for index, row in data.iterrows():
        context = row.get("Context", "")
        question = row.get("Question", "")
        answer = row.get("Answer", "")
        ref_context = row.get("Reference Content", "")
        ref_answer = row.get("Reference Answer", "")

        # Define lenses using Trulens's `Lens` class
        context_lens = Lens(lambda x: context)
        question_lens = Lens(lambda x: question)
        answer_lens = Lens(lambda x: answer)

        # Feedback configuration using these lenses
        feedback_function = Feedback(CustomFeedback().custom_metric_score).on(
            answer=answer_lens,
            question=question_lens,
            context=context_lens
        )

        # Set up TruChain for evaluation
        tru_chain = TruChain(
            chain=feedback_function,
            app_id="trulens_eval_app"
        )

        # Run the chain and collect results
        with tru_chain as recording:
            result = tru_chain.invoke({
                "answer": answer,
                "context": context,
                "question": question
            })

        # Collect feedback using Tru
        tru = Tru()
        records, feedback = tru.get_records_and_feedback(app_ids=[])

        # Process evaluation results
        for fb, fb_result in records.items():
            results.append({
                "Context": context,
                "Question": question,
                "Answer": answer,
                "Reference Context": ref_context,
                "Reference Answer": ref_answer,
                "Score": fb_result.result,
                "Reason": fb_result.calls[0].meta.get("reason", "No reason provided")
            })

    # Convert results into a DataFrame
    return pd.DataFrame(results)





# Streamlit UI
st.set_page_config(
    page_title="Trulens Evaluation",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("Trulens Evaluation with Excel Data")
st.write("""
Upload an Excel file containing `Context`, `Question`, `Answer`, `Reference Content`, and `Reference Answer`.
The system will evaluate these pairs using Trulens metrics and generate a results table with scores and explanations.
""")

# File uploader
uploaded_file = st.file_uploader(
    "Upload your evaluation data in Excel format:", type=["xlsx", "csv"]
)

if uploaded_file:
    with st.spinner("Processing uploaded data and running evaluation..."):
        # Read the uploaded Excel file
        if uploaded_file.name.endswith(".xlsx"):
            data = pd.read_excel(uploaded_file)
        else:
            data = pd.read_csv(uploaded_file)

        # Check for required columns
        if all(col in data.columns for col in ["Context", "Question", "Answer", "Reference Content", "Reference Answer"]):
            # Process uploaded data
            result_df = process_excel_data(data)

            # Display results
            st.subheader("Evaluation Results")
            st.write(
                "Below is the evaluation table showing metrics calculated using Trulens feedback."
            )
            st.dataframe(result_df)

        else:
            st.error(
                "The uploaded file must contain the following columns: `Context`, `Question`, `Answer`, `Reference Content`, `Reference Answer`."
            )

else:
    st.info(
        "Please upload a valid Excel file to evaluate data with Trulens metrics."
    )
