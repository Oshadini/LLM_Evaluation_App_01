import streamlit as st
import pandas as pd
import re
import openai

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

def evaluate_metric(system_prompt: str, df: pd.DataFrame, selected_columns: list) -> pd.DataFrame:
    """
    Evaluate the selected metric using GPT-4 based on the user-provided or generated system prompt.
    """
    column_mapping = {
        "User Input": "user_input",
        "Agent Prompt": "agent_prompt",
        "Agent Response": "agent_response",
    }
    
    results = []
    for index, row in df.iterrows():
        try:
            # Construct evaluation prompt for GPT-4
            evaluation_prompt = (
                f"System Prompt: {system_prompt}\n\n"
                f"Index: {row['Index']}\n"
                f"{', '.join([f'{col}: {row[col]}' for col in selected_columns])}\n\n"
                "Provide the following evaluation:\n"
                "- Score: Rate the quality of the agent's response on a scale of 1-10.\n"
                "- Criteria: Describe the criteria used for this evaluation.\n"
                "- Supporting Evidence: Justify the score using details from the input.\n"
                "- Tool Triggered: Identify any tools triggered by the agent."
            )
            
            # Call GPT-4 API
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an evaluator analyzing agent conversations."},
                    {"role": "user", "content": evaluation_prompt}
                ]
            )
            
            response_content = completion.choices[0].message.content.strip()
            
            # Parse GPT-4 response
            parsed_response = {
                "Index": row["Index"],
                "Metric": "",
                "Selected Columns": ", ".join(selected_columns),
                "Score": "",
                "Criteria": "",
                "Supporting Evidence": "",
                "Tool Triggered": "",
                "User Input": row["User Input"],
                "Agent Prompt": row["Agent Prompt"],
                "Agent Response": row["Agent Response"]
            }
            
            for line in response_content.split("\n"):
                if line.startswith("Score:"):
                    parsed_response["Score"] = line.replace("Score:", "").strip()
                elif line.startswith("Criteria:"):
                    parsed_response["Criteria"] = line.replace("Criteria:", "").strip()
                elif line.startswith("Supporting Evidence:"):
                    parsed_response["Supporting Evidence"] = line.replace("Supporting Evidence:", "").strip()
                elif line.startswith("Tool Triggered:"):
                    parsed_response["Tool Triggered"] = line.replace("Tool Triggered:", "").strip()
            
            results.append(parsed_response)
        
        except Exception as e:
            results.append({
                "Index": row["Index"],
                "Metric": "Error",
                "Selected Columns": ", ".join(selected_columns),
                "Score": "N/A",
                "Criteria": "Error",
                "Supporting Evidence": f"Error processing row: {e}",
                "Tool Triggered": "N/A",
                "User Input": row["User Input"],
                "Agent Prompt": row["Agent Prompt"],
                "Agent Response": row["Agent Response"]
            })
    return pd.DataFrame(results)

# Streamlit UI
st.title("LLM Conversation Evaluation Tool")
st.write("Upload an Excel or CSV file with headers: Index, User Input, Agent Prompt, and Agent Response to evaluate the conversation.")

uploaded_file = st.file_uploader("Upload your file", type=["xlsx", "csv"])

if uploaded_file:
    try:
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

            num_metrics = st.number_input("Enter the number of metrics to define:", min_value=1, step=1)

            # Store prompts and results in session state
            if "system_prompts" not in st.session_state:
                st.session_state.system_prompts = {}
            if "combined_results" not in st.session_state:
                st.session_state.combined_results = []

            for i in range(num_metrics):
                st.markdown(f"### Metric {i + 1}")

                selected_columns = st.multiselect(
                    f"Select columns for Metric {i + 1}:",
                    options=required_columns[1:],
                    key=f"columns_{i}"
                )

                toggle_prompt = st.checkbox(
                    f"Automatically generate system prompt for Metric {i + 1}", key=f"toggle_prompt_{i}"
                )

                if toggle_prompt:
                    if len(selected_columns) < 1:
                        st.error(f"For Metric {i + 1}, please select at least one column.")
                    else:
                        if f"metric_{i}" not in st.session_state.system_prompts:
                            try:
                                selected_column_names = ", ".join(selected_columns)
                                completion = openai.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "You are a helpful assistant generating system prompts."},
                                        {"role": "user", "content": f"Generate a concise system prompt to evaluate the conversation based on the columns: {selected_column_names}."}
                                    ]
                                )
                                system_prompt = completion.choices[0].message.content.strip()
                                st.session_state.system_prompts[f"metric_{i}"] = system_prompt
                            except Exception as e:
                                st.error(f"Error generating system prompt: {e}")

                        system_prompt = st.session_state.system_prompts.get(f"metric_{i}", "")
                        st.text_area(
                            f"Generated System Prompt for Metric {i + 1}:", value=system_prompt, height=150
                        )
                        st.success(f"System Prompt for Metric {i + 1} is valid.")
                else:
                    system_prompt = st.text_area(
                        f"Enter the System Prompt for Metric {i + 1}:",
                        height=150
                    )

                if st.button(f"Generate Results for Metric {i + 1}", key=f"generate_results_{i}"):
                    if system_prompt.strip() == "":
                        st.error(f"Please enter or generate a system prompt for Metric {i + 1}.")
                    else:
                        st.write(f"Generating results for Metric {i + 1}. Please wait...")
                        results_df = evaluate_metric(system_prompt, df, selected_columns)
                        results_df["Metric"] = f"Metric {i + 1}"
                        st.session_state.combined_results.extend(results_df.to_dict("records"))
                        st.write(f"Results for Metric {i + 1}:")
                        st.dataframe(results_df)

            if num_metrics > 1 and st.button("Generate Combined Results"):
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
