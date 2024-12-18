import streamlit as st
import pandas as pd
import openai

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define function to evaluate conversation using GPT-4
def evaluate_conversation(system_prompt: str, selected_columns: list, conversation: pd.DataFrame, metric_name: str) -> list:
    """
    Evaluate the conversation using GPT-4 based on the system prompt provided by the user.
    """
    results = []
    for index, row in conversation.iterrows():
        try:
            # Construct the evaluation prompt for GPT-4
            evaluation_prompt = f"""
            System Prompt: {system_prompt}

            Index: {row['Index']}
            Conversation: {row['Conversation']}
            Agent Prompt: {row['Agent Prompt']}

            Evaluate the entire conversation for Agent-Goal Accuracy. Use the following format:

            Criteria: [Explain what are the criterias used for the evaluation]
            Supporting Evidence: [Explain how well the Agent responded to the User's input and fulfilled their goals and highlight specific faulty or insufficient responses from the Agent]
            Score: [Provide a numerical or qualitative score here]
            """

            # Call GPT-4 API
            completion = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an evaluator analyzing agent conversations."},
                    {"role": "user", "content": evaluation_prompt}
                ]
            )

            response_content = completion.choices[0].message.content.strip()
            st.write(response_content)

            # Parse GPT-4 response
            parsed_response = {
                "Index": row["Index"],
                "Metric": metric_name,
                "Selected Columns": ", ".join(selected_columns),
                "Score": "",
                "Criteria": "",
                "Supporting Evidence": "",
                "Agent Prompt": row.get("Agent Prompt", ""),
                "Conversation": row.get("Conversation", "")
            }

            try:
                for line in response_content.split("\n"):
                    line = line.strip()
                    if line.startswith("Criteria:"):
                        parsed_response["Criteria"] = line.replace("Criteria:", "").strip()
                    elif line.startswith("Supporting Evidence:"):
                        parsed_response["Supporting Evidence"] = line.replace("Supporting Evidence:", "").strip()
                    elif line.startswith("Score:"):
                        parsed_response["Score"] = line.replace("Score:", "").strip()
            except Exception as e:
                parsed_response["Criteria"] = "Error"
                parsed_response["Supporting Evidence"] = f"Error parsing GPT-4 response: {e}"
                parsed_response["Score"] = "N/A"

            results.append(parsed_response)

        except Exception as e:
            results.append({
                "Index": row["Index"],
                "Metric": metric_name,
                "Selected Columns": ", ".join(selected_columns),
                "Score": "N/A",
                "Criteria": "Error",
                "Supporting Evidence": f"Error processing conversation: {e}",
                "Agent Prompt": row.get("Agent Prompt", ""),
                "Conversation": row.get("Conversation", "")
            })

    return results

# Hardcoded system prompt
HARDCODED_PROMPT = """
You are a AGENT-GOAL ACCURACY grader tasked with assessing the AGENT-GOAL ACCURACY of the provided CONVERSATION in relation to the given AGENT PROMPT. Your evaluation must adhere strictly to the following guidelines.

The primary goal is to assign a AGENT-GOAL ACCURACY score that reflects how well the AGENT RESPONSES provided in CONVERSATION align with the AGENT PROMPT. This evaluation focuses solely on the quality, completeness, and helpfulness of the information provided in the AGENT RESPONSES in CONVERSATION in addressing the AGENT PROMPT.

You must respond only with a single number from 0 to 10. No elaboration, justification, or additional text should accompany the score.

The AGENT-GOAL ACCURACY score ranges from 0 (least relevant) to 10 (most relevant). Use the following detailed criteria to determine the score.

- 0: The AGENT RESPONSES in CONVERSATION are entirely unrelated to the AGENT PROMPT. There is no evidence of any alignment, context, or attempt to address the AGENT PROMPT.
- 1 to 4: The AGENT RESPONSES in CONVERSATION address only a small portion of the AGENT PROMPT. The provided information lacks depth, precision, or sufficient context to be significantly helpful.
- 1-2: Minimal or superficial AGENT-GOAL ACCURACY; only a negligible portion of AGENT PROMPT is addressed.
- 3-4: Some AGENT-GOAL ACCURACY, but the coverage remains incomplete or only partially addresses the AGENT PROMPT.
- 5 to 8: The AGENT RESPONSES in CONVERSATION address most of the AGENT PROMPT with a reasonable level of helpfulness. The information provided is clear, relevant, and covers the majority of the AGENT PROMPT.
- 5-6: Covers most of the AGENT PROMPT, but some important areas remain insufficiently addressed.
- 7-8: Strong coverage and alignment with AGENT PROMPT, with minor gaps or lack of completeness.
- 9 to 10: The AGENT RESPONSES in CONVERSATION are comprehensively aligned with the AGENT PROMPT. The information provided is precise, complete, and entirely relevant to all parts of the AGENT PROMPT. The content is not only accurate but also helpful and sufficient to address the entire AGENT PROMPT.
- 9: Near-perfect alignment; only very minor omissions or imperfections exist.
- 10: Fully relevant with no gaps; the AGENT RESPONSES in CONVERSATION are complete, precise, and entirely sufficient to address every aspect of the AGENT PROMPT.

Criteria: The evaluation must consider specific factors when determining the AGENT-GOAL ACCURACY score. These factors include how well the AGENT RESPONSES address the USER INPUTS, the accuracy and helpfulness of the responses in relation to the AGENT PROMPT, and whether the information provided is sufficiently complete and precise to satisfy the context of the AGENT PROMPT.

Supporting Evidence: To provide a comprehensive evaluation, it is necessary to identify and highlight areas of strong alignment where the Agent fulfilled the User’s goals as well as specific faulty or insufficient responses that detract from the overall relevance. Examples of such insufficiencies include cases where the Agent misunderstood the User’s intent, provided inaccurate or incomplete information, or failed to offer meaningful assistance.
"""

# Streamlit UI
st.write("Upload an Excel or CSV file with headers: Index, Conversation, and Agent Prompt to evaluate the conversation.")

uploaded_file = st.file_uploader("Upload your file", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Read uploaded file
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        required_columns = ["Index", "Conversation", "Agent Prompt"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"The uploaded file must contain these columns: {', '.join(required_columns)}.")
        else:
            st.write("Preview of Uploaded Data:")
            st.dataframe(df.head())

            num_metrics = st.number_input("Enter the number of metrics you want to define:", min_value=1, step=1)

            if "system_prompts" not in st.session_state:
                st.session_state.system_prompts = {}
            if "combined_results" not in st.session_state:
                st.session_state.combined_results = []

            for i in range(num_metrics):
                st.markdown(f"""
                    <hr style="border: 5px solid #000000;">
                    <h3 style="background-color: #f0f0f0; padding: 10px; border: 2px solid #000000;">
                        Metric {i + 1}
                    </h3>
                """, unsafe_allow_html=True)

                selected_columns = st.multiselect(
                    f"Select columns for Metric {i + 1}:",
                    options=required_columns[1:],  # Skip the Index column
                    key=f"columns_{i}"
                )

                toggle_prompt = st.checkbox(
                    f"Use predefined system prompt for Metric {i + 1}", key=f"toggle_prompt_{i}"
                )

                if toggle_prompt:
                    system_prompt = HARDCODED_PROMPT
                    st.text_area(
                        f"System Prompt for Metric {i + 1} (Predefined):",
                        value=system_prompt,
                        height=300,
                        disabled=True
                    )
                else:
                    system_prompt = st.text_area(
                        f"Enter the System Prompt for Metric {i + 1}:",
                        height=200
                    )

                if st.button(f"Metric {i + 1} Results", key=f"generate_results_{i}"):
                    if system_prompt.strip() == "":
                        st.error("Please enter a valid system prompt.")
                    else:
                        st.write("Evaluating conversations. Please wait...")
                        results = evaluate_conversation(system_prompt, selected_columns, df, f"Metric {i + 1}")
                        st.session_state.combined_results.extend(results)
                        st.write(f"Results for Metric {i + 1}:")
                        st.dataframe(pd.DataFrame(results))

            if num_metrics > 1 and st.button("Overall Results"):
                if st.session_state.combined_results:
                    combined_df = pd.DataFrame(st.session_state.combined_results)
                    st.write("Combined Results:")
                    st.dataframe(combined_df)
                    st.download_button(
                        label="Download Combined Results as CSV",
                        data=combined_df.to_csv(index=False),
                        file_name="combined_evaluation_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No results to combine. Please generate results for individual metrics first.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
