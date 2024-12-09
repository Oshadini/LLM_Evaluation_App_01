import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval import Feedback, TruChain, Tru
from typing import Optional, Dict, Tuple


# Custom feedback class that defines the scoring logic
class CustomFeedback(OpenAI):
    """
    Extend OpenAI's functionality for feedback with custom metric scoring logic.
    """
    def custom_metric_score(self, answer: Optional[str] = None, question: Optional[str] = None, context: Optional[str] = None) -> Tuple[float, Dict]:
        """
        This method defines a scoring logic based on relevance or any custom logic you require.
        """
        if answer and question and context:
            # Simple placeholder scoring logic; replace with actual scoring logic
            score = 7.0  # Dummy fixed score (replace this logic as needed)
            return score, {"reason": "Scored based on custom relevance logic"}
        return 0.0, {"reason": "Default fallback score"}


def process_excel_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Processes uploaded data and performs Trulens evaluation on each row.
    Returns a DataFrame with results for visualization.
    """
    results = []
    
    # Instantiate your custom feedback class
    feedback_provider = CustomFeedback()

    for index, row in data.iterrows():
        context = row.get("Context", "")
        question = row.get("Question", "")
        answer = row.get("Answer", "")
        ref_context = row.get("Reference Content", "")
        ref_answer = row.get("Reference Answer", "")
        
        # Use feedback logic from custom feedback provider
        feedback_function = Feedback(feedback_provider.custom_metric_score).on(
            answer=lambda x: answer,
            question=lambda x: question,
            context=lambda x: context
        )

        # Set up TruChain for evaluation
        tru_chain = TruChain(
            chain=feedback_function,
            app_id="trulens_eval_app"
        )

        # Run evaluation
        with tru_chain as recording:
            result = tru_chain.invoke({
                "answer": answer,
                "context": context,
                "question": question
            })

        # Collect feedback
        tru = Tru()
        records, feedback = tru.get_records_and_feedback(app_ids=[])

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
