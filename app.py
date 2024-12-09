import streamlit as st
import pandas as pd
from trulens_eval import Feedback, Select, Tru, TruChain
from trulens_eval.feedback.provider import OpenAI
from typing import Optional, Dict, Tuple
from trulens_eval.app import App

class CustomFeedback:
    def __init__(self, chain):
        self.feedbacks = []
        self.chain = chain

    def add_feedback(self, metric_name, prompt, combination):
        self.feedbacks.append({"metric_name": metric_name, "prompt": prompt, "combination": combination})

    def evaluate(self, data):
        results = []
        for feedback in self.feedbacks:
            metric_name = feedback["metric_name"]
            prompt = feedback["prompt"]
            combination = feedback["combination"]

            # Generate a custom prompt using the selected combination of inputs
            input_text = "\n".join([f"{col}: {data[col]}" for col in combination if col in data])
            full_prompt = f"{prompt}\n\n{input_text}"

            # Evaluate using Trulens feedback
            f_custom_function = (
                Feedback(Custom_FeedBack(self.chain).custom_metric_score)
                .on(answer=Select.RecordOutput)
                .on(question=Select.RecordInput)
                .on(context=input_text)
            )

            tru_recorder = TruChain(self.chain, feedbacks=[f_custom_function])

            with tru_recorder as recording:
                self.chain.invoke(full_prompt)

            # Fetch results
            record = recording.get()
            for fb, fb_result in record.wait_for_feedback_results().items():
                if fb.name == "custom_metric_score":
                    results.append({
                        "metric": metric_name,
                        "score": fb_result.result,
                        "explanation": fb_result.calls[0].meta.get("reason", "No explanation provided")
                    })

        return results

class Custom_FeedBack(OpenAI):
    def custom_metric_score(self, answer: Optional[str] = None, question: Optional[str] = None, context: Optional[any] = None) -> Tuple[float, Dict]:
        professional_prompt = f"where 0 is not at all related and 10 is extremely related:\n\n"
        
        if answer:
            professional_prompt += f"Answer: {answer}\n"
        if question:
            professional_prompt += f"Question: {question}\n"
        if context:
            professional_prompt += f"Context: {context}\n"

        user_prompt = professional_prompt
        return self.generate_score_and_reasons(system_prompt="RELEVANCE", user_prompt=user_prompt)

st.set_page_config(page_title="Custom Metrics Evaluation", page_icon="📊", layout="wide")
st.title("Custom Metrics Evaluation")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
if uploaded_file:
    data = pd.read_excel(uploaded_file)
    st.write("File Loaded:")
    st.dataframe(data)

    # User input: Number of metrics
    num_metrics = st.number_input("How many metrics do you want to define?", min_value=1, max_value=10, step=1)

    chain = ChatopenAI(model="gpt-4o", openai_api_key=st.secrets["OPENAI_API_KEY"], max_tokens=1024)
    feedback = CustomFeedback(chain)

    metric_tabs = st.tabs([f"Metric {i+1}" for i in range(num_metrics)])
    for i, tab in enumerate(metric_tabs):
        with tab:
            st.subheader(f"Define Metric {i+1}")
            metric_name = st.text_input(f"Metric Name for Metric {i+1}")
            columns = st.multiselect(f"Select input combinations for Metric {i+1}", options=data.columns)
            custom_prompt = st.text_area(f"Custom Prompt for Metric {i+1}")
            feedback.add_feedback(metric_name, custom_prompt, columns)

    if st.button("Evaluate Metrics"):
        st.subheader("Evaluation Results")
        for index, row in data.iterrows():
            results = feedback.evaluate(row.to_dict())
            st.markdown(f"### Row {index + 1} Results")
            for result in results:
                st.write(f"**Metric:** {result['metric']}")
                st.write(f"**Score:** {result['score']}")
                st.write(f"**Explanation:** {result['explanation']}")
                st.divider()
