# File path: app.py

import streamlit as st
import pandas as pd
from trulens_eval.feedback.provider import OpenAI
from trulens_eval.feedback import prompts
from trulens_eval import Feedback, Select, Tru, TruChain
from trulens_eval.app import App


# Initialize Trulens
tru = Tru()
tru_chain = TruChain(steps=[OpenAI(api_key=st.secrets["OPENAI_API_KEY"])])


class CustomFeedback:
    """
    Custom feedback class to handle Trulens evaluation logic.
    """
    def __init__(self):
        self.tru_chain = tru_chain

    def evaluate_prompt(self, prompt: str, generated: str) -> (float, str):
        """
        Evaluate using Trulens without invoking GPT for evaluation.
        :param prompt: User-provided prompt context.
        :param generated: The LLM-generated response.
        :return: A feedback score and explanation from Trulens pipeline.
        """
        try:
            # Invoke Trulens feedback mechanism with the prompt & generated response.
            feedback_result = self.tru_chain.invoke({
                "prompt": prompt,
                "response": generated
            })
            # Extract score and explanation
            score = feedback_result.feedback_score if feedback_result else 0.0
            explanation = feedback_result.explanation if feedback_result else "No explanation provided."
            return score, explanation
        except Exception as e:
            st.error(f"Error during feedback evaluation: {e}")
            return 0.0, f"Error evaluating feedback: {str(e)}"


# Define the main function for Streamlit app
def main():
    st.title("Custom Metric Analysis Application with Trulens")

    # Section: Upload Input File
    uploaded_file = st.file_uploader(
        "Upload an Excel file to provide input data for analysis", type=["xlsx"]
    )
    if uploaded_file:
        # Load the uploaded data
        data = pd.read_excel(uploaded_file)
        st.write("Preview of Uploaded Data:")
        st.dataframe(data)

        # Extract column names for interactivity
        columns = list(data.columns)

        # Allow user to define metrics for evaluation
        st.header("Define Metrics for Evaluation")
        num_metrics = st.number_input(
            "How many metrics would you like to define?", min_value=1, step=1, value=1
        )

        metrics = {}
        # Allow user to select relevant columns and define prompts for Trulens evaluation
        for i in range(1, num_metrics + 1):
            st.subheader(f"Define Metric {i}")
            selected_columns = st.multiselect(
                f"Select relevant columns for Metric {i}:",
                options=columns,
                key=f"metric_{i}_columns"
            )
            metric_prompt = st.text_input(
                f"Define the prompt for Metric {i}:",
                key=f"metric_{i}_prompt"
            )
            if selected_columns and metric_prompt:
                metrics[f"Metric {i}"] = {
                    "columns": selected_columns,
                    "prompt": metric_prompt
                }

        # Allow user to compute results after defining the metrics
        if st.button("Evaluate Metrics with Trulens"):
            st.subheader("Processing Metrics using Trulens")
            results = []
            feedback_engine = CustomFeedback()

            for metric_name, metric_info in metrics.items():
                try:
                    # Get relevant data from the uploaded file
                    selected_data = data[metric_info["columns"]].dropna(how='any')
                    for index, row in selected_data.iterrows():
                        # Combine data into context for evaluation
                        combined_context = " ".join(row.astype(str))

                        # Use Trulens feedback mechanism to evaluate context
                        score, explanation = feedback_engine.evaluate_prompt(
                            prompt=metric_info["prompt"],
                            generated=combined_context
                        )

                        # Log results
                        results.append({
                            "Metric": metric_name,
                            "Context": combined_context,
                            "Score": score,
                            "Explanation": explanation
                        })

                    # Convert the results to a DataFrame for visualization
                    result_df = pd.DataFrame(results)
                    st.write(result_df)

                    # Allow user to download the evaluation results as a CSV
                    csv_data = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_data,
                        file_name="evaluation_results.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error processing metrics for {metric_name}: {e}")


# Run the Streamlit app
if __name__ == "__main__":
    main()
