import streamlit as st
import pandas as pd
import openai
import re

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

def evaluate_conversation(system_prompt: str, selected_columns: list, conversation: pd.DataFrame, metric_name: str) -> list:
    results = []
    for index, row in conversation.iterrows():
        try:
            evaluation_prompt = f"""
            You are an AGENT-GOAL ACCURACY grader tasked with assessing the AGENT-GOAL ACCURACY of the provided CONVERSATION in relation to the given AGENT PROMPT.

            Only respond with a single integer number between 0 and 10. Do not include any additional text or explanation. Adhere strictly to these guidelines.

            Index: {row['Index']}
            Conversation: {row['Conversation']}
            Agent Prompt: {row['Agent Prompt']}
            """

            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an evaluator analyzing agent conversations."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                max_tokens=10,
                temperature=0.0
            )

            response_content = completion.choices[0].message.content.strip()
            st.write(f"Raw Response: {response_content}")

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
                # Validate and parse numeric response
                match = re.match(r"^\d+(\.\d+)?$", response_content)
                if match:
                    parsed_response["Score"] = response_content
                else:
                    parsed_response["Score"] = "Error"
                    parsed_response["Supporting Evidence"] = f"Invalid response format: {response_content}"
            except Exception as e:
                parsed_response["Score"] = "Error"
                parsed_response["Supporting Evidence"] = f"Parsing error: {e}"

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

# Remaining Streamlit UI logic remains unchanged
