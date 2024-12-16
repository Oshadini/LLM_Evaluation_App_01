import streamlit as st
import pandas as pd
import re
import openai

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define function to evaluate conversation using GPT-4
def evaluate_conversation(system_prompt: str, conversation: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluate the conversation using GPT-4 based on the system prompt provided by the user.
    """
    results = []
    for index, row in conversation.iterrows():
        try:
            # Construct the evaluation prompt for GPT-4
            evaluation_prompt = (
                f"System Prompt: {system_prompt}\n\n"
                f"Index: {row['Index']}\n"
                f"User Input: {row['User Input']}\n"
                f"Agent Prompt: {row['Agent Prompt']}\n"
                f"Agent Response: {row['Agent Response']}\n\n"
                f"Provide the following evaluation: \n"
                f"- Criteria: Evaluate the quality of the agent's response.\n"
                f"- Supporting Evidence: Justify your evaluation with evidence from the conversation.\n"
                f"- Tool Triggered: Identify any tools triggered during the response.\n"
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
                "Criteria": "",
                "Supporting Evidence": "",
                "Tool Triggered": "",
                "User Input": row["User Input"],
                "Agent Prompt": row["Agent Prompt"],
                "Agent Response": row["Agent Response"]
            }
            
            for line in response_content.split("\n"):
                if line.startswith("Criteria:"):
                    parsed_response["Criteria"] = line.replace("Criteria:", "").strip()
                elif line.startswith("Supporting Evidence:"):
                    parsed_response["Supporting Evidence"] = line.replace("Supporting Evidence:", "").strip()
                elif line.startswith("Tool Triggered:"):
                    parsed_response["Tool Triggered"] = line.replace("Tool Triggered:", "").strip()
            
            results.append(parsed_response)
        
        except Exception as e:
            results.append({
                "Index": row["Index"],
                "Criteria": "Error",
                "Supporting Evidence": f"Error processing conversation: {e}",
                "Tool Triggered": "N/A",
                "User Input": row["User Input"],
                "Agent Prompt": row["Agent Prompt"],
                "Agent Response": row["Agent Response"]
            })
    return pd.DataFrame(results)

# Streamlit UI
st.title("LLM Conversation Evaluation Tool")
st.write("Upload an Excel file with headers: Index, User Input, Agent Prompt, and Agent Response to evaluate the conversation.")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        required_columns = ["Index", "User Input", "Agent Prompt", "Agent Response"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"The uploaded file must contain these columns: {', '.join(required_columns)}.")
        else:
            st.write("Preview of Uploaded Data:")
            st.dataframe(df.head())

            system_prompt = st.text_area(
                "Enter the System Prompt to evaluate the conversation:",
                height=200
            )

            if st.button("Evaluate Conversations"):
                if system_prompt.strip() == "":
                    st.error("Please enter a valid system prompt.")
                else:
                    st.write("Evaluating conversations. Please wait...")
                    results_df = evaluate_conversation(system_prompt, df)
                    st.write("Evaluation Results:")
                    st.dataframe(results_df)
                    st.download_button(
                        label="Download Results as CSV",
                        data=results_df.to_csv(index=False),
                        file_name="conversation_evaluation_results.csv",
                        mime="text/csv"
                    )
    except Exception as e:
        st.error(f"An error occurred: {e}")
