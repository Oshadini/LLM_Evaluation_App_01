import streamlit as st
import pandas as pd
import re
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
            evaluation_prompt = f"System Prompt: {system_prompt}\n\n"
            evaluation_prompt += f"Index: {row['Index']}\n"
            evaluation_prompt += f"User Input: {row['User Input']}\n"
            evaluation_prompt += f"Agent Prompt: {row['Agent Prompt']}\n"
            evaluation_prompt += f"Agent Response: {row['Agent Response']}\n\n"
            evaluation_prompt += (
                "Provide the following evaluation:\n"
                "- Criteria: Evaluate the quality of the agent's response.\n"
                "- Supporting Evidence: Justify your evaluation with evidence from the conversation.\n"
                "- Tool Triggered: Identify any tools triggered during the response.\n"
                "- Score: Provide an overall score for the response.\n"
            )

            # Call GPT-4 API
            completion = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an evaluator analyzing agent conversations."},
                    {"role": "user", "content": evaluation_prompt}
                ]
            )

            response_content = completion.choices[0].message.content.strip()

            # Parse the response
            parsed_response = {
                "Index": row["Index"],
                "Metric": metric_name,
                "Selected Columns": ", ".join(selected_columns),
                "Score": "",
                "Criteria": "",
                "Supporting Evidence": "",
                "Tool Triggered": "",
                "User Input": row.get("User Input", ""),
                "Agent Prompt": row.get("Agent Prompt", ""),
                "Agent Response": row.get("Agent Response", "")
            }

            for line in response_content.split("\n"):
                if line.startswith("Criteria:"):
                    parsed_response["Criteria"] = line.replace("Criteria:", "").strip()
                elif line.startswith("Supporting Evidence:"):
                    parsed_response["Supporting Evidence"] = line.replace("Supporting Evidence:", "").strip()
                elif line.startswith("Tool Triggered:"):
                    parsed_response["Tool Triggered"] = line.replace("Tool Triggered:", "").strip()
                elif line.startswith("Score:"):
                    parsed_response["Score"] = line.replace("Score:", "").strip()

            results.append(parsed_response)

        except Exception as e:
            results.append({
                "Index": row["Index"],
                "Metric": metric_name,
                "Selected Columns": ", ".join(selected_columns),
                "Score": "N/A",
                "Criteria": "Error",
                "Supporting Evidence": f"Error processing conversation: {e}",
                "Tool Triggered": "N/A",
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
                                        {"role": "user", "content": f"Generate a system prompt less than 200 tokens to evaluate relevance based on the following columns: {selected_column_names}."}
                                    ],
                                    max_tokens=200
                                )
                                system_prompt = completion.choices[0].message.content.strip()
                                st.wrtite(system_prompt)
                                st.session_state.system_prompts[f"metric_{i}"] = system_prompt
                            except Exception as e:
                                st.error(f"Error generating or processing system prompt: {e}")

                        system_prompt = st.session_state.system_prompts.get(f"metric_{i}", "")
                        st.text_area(
                            f"Generated System Prompt for Metric {i + 1}:", value=system_prompt, height=200
                        )
                        st.success(f"System Prompt for Metric {i + 1} is valid.")
                else:
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
                        st.write(results)
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
