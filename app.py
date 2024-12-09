import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.utils.generated import re_0_10_rating
from trulens_eval import Feedback, TruChain, Tru
from typing import Optional, Dict, Tuple



from trulens_eval.feedback import Feedback


# Load Trulens's Feedback Class
class CustomFeedback:
    def __init__(self):
        self.feedbacks = []

    def add_feedback(self, metric_name, prompt, combination):
        self.feedbacks.append({"metric_name": metric_name, "prompt": prompt, "combination": combination})

    def evaluate(self, data):
        results = []
        for feedback in self.feedbacks:
            prompt = feedback["prompt"]
            combination = feedback["combination"]

            # Generate a custom prompt using the selected combination of inputs
            input_text = "\n".join([f"{col}: {data[col]}" for col in combination if col in data])
            full_prompt = f"""
                {prompt}
                
                Given the input data below:
                {input_text}

                Please return a response in JSON format with the following structure:
                {{
                    "score": <numeric value or string>,
                    "reason": <short explanation of the score>
                }}
            """

            # Send the prompt to the model
            try:
                response = model.invoke(full_prompt)

                # Safely parse response
                if hasattr(response, 'content'):
                    response_content = response.content
                    try:
                        # Parse as JSON
                        parsed_result = json.loads(response_content)
                        results.append({
                            "metric": feedback["metric_name"],
                            "score": parsed_result.get("score", "N/A"),
                            "explanation": parsed_result.get("reason", "No explanation provided"),
                        })
                    except json.JSONDecodeError:
                        # Handle plain-text response
                        results.append({
                            "metric": feedback["metric_name"],
                            "score": "N/A",
                            "explanation": f"Plain text response: {response_content}",
                        })
                else:
                    results.append({
                        "metric": feedback["metric_name"],
                        "score": "N/A",
                        "explanation": "Invalid response format",
                    })
            except Exception as e:
                results.append({
                    "metric": feedback["metric_name"],
                    "score": "N/A",
                    "explanation": f"Error during evaluation: {str(e)}",
                })

        return results



# Instantiate Trulens Feedback
#custom_feedback = CustomFeedback()


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
        
        # Configure feedback using Trulens's OpenAI feedback mechanism
        feedback_function = Feedback(OpenAI().custom_metric_score).on(
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
