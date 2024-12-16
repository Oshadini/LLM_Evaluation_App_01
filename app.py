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
    for _, row in conversation.iterrows():
        try:
            # Construct the evaluation prompt for GPT-4
            evaluation_prompt = f"{system_prompt}\n\n"
            evaluation_prompt += f"Conversation:\n"
            evaluation_prompt += f"- User Input: {row['User Input']}\n"
            evaluation_prompt += f"- Agent Prompt: {row['Agent Prompt']}\n"
            evaluation_prompt += f"- Agent Response: {row['Agent Response']}\n"
            evaluation_prompt += "\nProvide the following evaluation:\n"
            evaluation_prompt += "- Criteria: Evaluate the quality of the agent's response.\n"
            evaluation_prompt += "- Supporting Evidence: Justify your evaluation with evidence from the conversation.\n"
            evaluation_prompt += "- Tool Triggered: Identify any tools triggered during the response.\n"
            evaluation_prompt += "- Score: Provide an overall score for the response (0-10).\n"

            # Call GPT-4 API
            completion = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an evaluator analyzing agent conversations."},
                    {"role": "user", "content": evaluation_prompt}
                ]
            )

            # Debug the raw response content
            response_content = completion.choices[0].message.content.strip()
            print(f"DEBUG: GPT-4 Response for Index {row['Index']}:\n{response_content}")

            # Initialize parsed response with default values
            parsed_response = {
                "Index": row["Index"],
                "Metric": metric_name,
                "Selected Columns": ", ".join(selected_columns),
                "Score": "N/A",
                "Criteria": "N/A",
                "Supporting Evidence": "N/A",
                "Tool Triggered": "N/A",
                "User Input": row.get("User Input", ""),
                "Agent Prompt": row.get("Agent Prompt", ""),
                "Agent Response": row.get("Agent Response", "")
            }

            # Extract fields robustly from the response
            for line in response_content.split("\n"):
                line = line.strip()  # Remove leading/trailing spaces
                if "Criteria:" in line:
                    parsed_response["Criteria"] = line.split("Criteria:", 1)[2].strip()
                elif "Supporting Evidence:" in line:
                    parsed_response["Supporting Evidence"] = line.split("Supporting Evidence:", 1)[2].strip()
                elif "Tool Triggered:" in line:
                    parsed_response["Tool Triggered"] = line.split("Tool Triggered:", 1)[2].strip()
                elif "Score:" in line:
                    parsed_response["Score"] = line.split("Score:", 1)[2].strip()

            # Log the parsed response
            print(f"DEBUG: Parsed Response for Index {row['Index']}: {parsed_response}")

            results.append(parsed_response)

        except Exception as e:
            # Append error details for this row
            error_message = f"Error processing conversation: {e}"
            print(f"DEBUG: {error_message} for Index {row['Index']}")

            results.append({
                "Index": row["Index"],
                "Metric": metric_name,
                "Selected Columns": ", ".join(selected_columns),
                "Score": "Error",
                "Criteria": "Error",
                "Supporting Evidence": error_message,
                "Tool Triggered": "Error",
                "User Input": row.get("User Input", ""),
                "Agent Prompt": row.get("Agent Prompt", ""),
                "Agent Response": row.get("Agent Response", "")
            })

    return results


# Streamlit UI
st.title("LLM Conversation Evaluation Tool")
st.write("Upload an Excel or CSV file with headers: Index, User Input, Agent Prompt, and Agent Response to evaluate the conversation.")

uploaded_file = st.file_uploader("Upload your file", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Read uploaded file
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        required_columns = ["Index", "User Input", "Agent Prompt", "Agent Response"]
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
                # Display metric setup
                st.markdown(f"""
                    <hr style="border: 5px solid #000000;">
                    <h3 style="background-color: #f0f0f0; padding: 10px; border: 2px solid #000000;">
                        Metric {i + 1}
                    </h3>
                """, unsafe_allow_html=True)

                # Column selection
                selected_columns = st.multiselect(
                    f"Select columns for Metric {i + 1}:",
                    options=required_columns[1:],  # Skip the Index column
                    key=f"columns_{i}"
                )

                # System prompt configuration
                system_prompt = st.text_area(
                    f"Enter the System Prompt for Metric {i + 1}:",
                    height=200
                )

                # Generate results for each metric
                if st.button(f"Generate Results for Metric {i + 1}", key=f"generate_results_{i}"):
                    if system_prompt.strip() == "":
                        st.error("Please enter a valid system prompt.")
                    elif len(selected_columns) == 0:
                        st.error("Please select at least one column.")
                    else:
                        st.write("Evaluating conversations. Please wait...")
                        results = evaluate_conversation(system_prompt, selected_columns, df, f"Metric {i + 1}")
                        st.session_state.combined_results.extend(results)
                        st.write(f"Results for Metric {i + 1}:")
                        st.dataframe(pd.DataFrame(results))

            # Combine results for all metrics
            if num_metrics > 1 and st.button("Generate Overall Results"):
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
