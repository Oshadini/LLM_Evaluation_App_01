# File path: app.py

import streamlit as st
import pandas as pd
import openai
from trulens_eval import Tru, TruChain, Feedback
from trulens_eval.feedback.provider import OpenAI as TruOpenAI


# Initialize OpenAI and TruLens
openai.api_key = st.secrets["OPENAI_API_KEY"]
tru = Tru()
feedback_provider = TruOpenAI(api_key=openai.api_key)


# Custom TruLens feedback evaluation logic
class CustomFeedback:
    def __init__(self):
        self.tru = Tru()
        self.tru_chain = TruChain(feedback_provider)

    def evaluate_prompt(self, prompt: str, generated: str) -> (float, str):
        """
        Evaluate the generated response using TruLens for scoring and explanation.
        :param prompt: The initial prompt used for context.
        :param generated: The GPT-generated response text.
        :return: A score and explanation derived from TruLens feedback.
        """
        # Evaluate feedback using TruLens tools
        try:
            # Perform evaluation using TruChain
            feedback = self.tru_chain.evaluate_single_feedback(
                prompt=prompt,
                generated=generated
            )

            # Extract score and explanation
            score = feedback.feedback_score  # Numeric score
            explanation = feedback.explanation  # Feedback explanation text

            # Ensure score is valid within [0,1]
            if 0 <= score <= 1:
                return score, explanation
            else:
                return 0.0, "Invalid feedback score range"
        except Exception as e:
            st.error(f"Error with TruLens evaluation: {e}")
            return 0.0, f"Error with TruLens evaluation: {str(e)}"


# Define the main function for the Streamlit app
def main():
    st.title("Custom Metric Analysis Application with TruLens")

    # Section: File Upload
    uploaded_file = st.file_uploader(
        "Upload an Excel file to provide input data for analysis", type=["xlsx"]
    )
    if uploaded_file:
        # Read uploaded Excel
        data = pd.read_excel(uploaded_file)
        st.write("Preview of Uploaded File:")
        st.dataframe(data)

        # Extract column names for user interaction
        columns = list(data.columns)

        # Allow user to define metrics
        st.header("Define Custom Metrics")
        num_metrics = st.number_input(
            "Number of metrics to evaluate", min_value=1, step=1, value=1
        )

        metrics = {}
        # User selects columns and defines custom prompts
        for i in range(1, num_metrics + 1):
            st.subheader(f"Metric {i}")
            selected_columns = st.multiselect(
                f"Select columns for Metric {i}:",
                options=columns,
                key=f"metric_{i}_columns"
            )
            metric_prompt = st.text_input(
                f"Enter prompt for Metric {i} (to evaluate context):",
                key=f"metric_{i}_prompt"
            )
            if selected_columns and metric_prompt:
                metrics[f"Metric {i}"] = {
                    "columns": selected_columns,
                    "prompt": metric_prompt
                }

        # Allow the user to compute results
        if st.button("Evaluate Metrics"):
            st.subheader("Processing Metrics...")
            results = []
            feedback_engine = CustomFeedback()

            for metric_name, metric_info in metrics.items():
                try:
                    # Use custom prompt logic and fetch data based on selected columns
                    selected_data = data[metric_info["columns"]].dropna(how='any')
                    for index, row in selected_data.iterrows():
                        # Combine relevant data from the rows into context
                        combined_context = " ".join(row.astype(str))

                        # Generate OpenAI response
                        try:
                            openai_response = openai.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "You are an assistant evaluating relevance."},
                                    {"role": "user", "content": f"{metric_info['prompt']} Context: {combined_context}"}
                                ],
                                max_tokens=100,
                                temperature=0.7
                            )
                            response_text = openai_response.choices[0].message.content.strip()
                        except Exception as e:
                            response_text = f"API error: {e}"

                        # Evaluate using TruLens (feedback pipeline)
                        score, explanation = feedback_engine.evaluate_prompt(
                            prompt=metric_info['prompt'],
                            generated=response_text
                        )

                        # Log result
                        results.append({
                            "Metric": metric_name,
                            "Context": combined_context,
                            "Generated Response": response_text,
                            "Score": score,
                            "Explanation": explanation
                        })

                    # Convert results to DataFrame for visualization
                    result_df = pd.DataFrame(results)
                    st.write(result_df)

                    # Enable download
                    csv_data = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv_data,
                        file_name="metric_results.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Processing error for {metric_name}: {e}")


# Run the app
if __name__ == "__main__":
    main()
