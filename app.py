import streamlit as st

# Set page config (must be first Streamlit command)
st.set_page_config(page_title="⚙️ LLM Evaluation Tool", layout="wide")

# Custom CSS for enhanced styling
st.markdown(
    """
    <style>
        /* Center align the sidebar content */
        [data-testid="stSidebar"] {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .stButton>button {
            border-radius: 8px;
            background-color: #4CAF50;
            color: white;
            padding: 8px 16px;
            font-size: 16px;
            font-weight: bold;
            margin: 10px auto; /* Center align the buttons */
            height: 40px;
            width: 150px;
            transition: background-color 0.3s ease, transform 0.2s ease;
        }

        .stButton>button:hover {
            background-color: #45a049;
            transform: scale(1.03);
        }

        .header-text {
            font-size: 30px;
            font-weight: bold;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 20px;
            color: #333333;
        }

        .section-box {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            background-color: #f9f9f9;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        /* Custom browser title styling */
        .streamlit-expanderHeader p {
            font-size: 16px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit App Title
st.markdown('<div class="header-text">LLM Evaluation Tool</div>', unsafe_allow_html=True)

# Use session state to track which button was clicked
if "active_page" not in st.session_state:
    st.session_state.active_page = "home"

# Sidebar Navigation
with st.sidebar:
    st.title("🧭 Navigation")

    # Run Code 1 and Code 2 buttons (Top Section)
    code1_col, code2_col = st.columns(2)
    with code1_col:
        if st.button("RAG Testing", key="code1_btn"):
            st.session_state.active_page = "code1"
    with code2_col:
        if st.button("Agentic Testing", key="code2_btn"):
            st.session_state.active_page = "code2"

    st.write("---")  # Divider to separate sections

    # Home and Exit buttons (Bottom Section)
    st.write("")  # Spacer
    st.write("")  # Spacer
    st.write("")  # Spacer
    st.write("")  # Spacer
    home_col, exit_col = st.columns(2)
    with home_col:
        if st.button("🏠 Home", key="home_btn"):
            st.session_state.active_page = "home"
    with exit_col:
        if st.button("🚪 Exit", key="exit_btn"):
            st.session_state.active_page = "exit"

# Display the selected page
if st.session_state.active_page == "home":
    # Home Page Content
    st.markdown(
        """
        <div class="section-box">
            <h2>Welcome to the LLM Evaluation Tool</h2>
            <p>Click on the navigation buttons to run RAG Testing or Agentic CAI Testing.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
elif st.session_state.active_page == "code1":
    # Full-Page Content for Code 1
    st.markdown('<div class="header-text"> RAG Testing </div>', unsafe_allow_html=True)
    #st.write("This is where Code 1 will execute.")
    #st.success("You are now viewing the full page for Code 1.")


    import streamlit as st
    import pandas as pd
    import re
    from typing import Tuple, Dict
    from trulens.core import Feedback
    from trulens.providers.openai import OpenAI as fOpenAI
    from trulens.core import TruSession
    from trulens.feedback import prompts
    import openai
    
    # Initialize the session
    session = TruSession()
    
    # Set OpenAI API key
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    
    # Define the custom class
    class prompt_with_conversation_relevence(fOpenAI):
        def prompt_with_conversation_relevence_feedback(self, **kwargs) -> Tuple[float, Dict]:
            """
            Process the dynamically selected parameters to generate relevance feedback.
            """
            user_prompt = ""
            if "question" in kwargs:
                user_prompt += "question: {question}\n\n"
            if "formatted_history" in kwargs:
                user_prompt += "answer: {formatted_history}\n\n"
            if "formatted_reference_context" in kwargs:
                user_prompt += "reference_context: {formatted_reference_context}\n\n"
            if "formatted_reference_answer" in kwargs:
                user_prompt += "reference_answer: {formatted_reference_answer}\n\n"
            if "formatted_context" in kwargs:
                user_prompt += "context: {formatted_context}\n\n"
            user_prompt += "RELEVANCE: "
    
            user_prompt = user_prompt.format(**kwargs)
    
            user_prompt = user_prompt.replace(
                "RELEVANCE:", prompts.COT_REASONS_TEMPLATE
            )
    
            result = self.generate_score_and_reasons(kwargs["system_prompt"], user_prompt)
    
            details = result[1]
            reason = details['reason'].split('\n')
            criteria = reason[0].split(': ')[1]
            supporting_evidence = reason[1].split(': ')[1]
            score = reason[-1].split(': ')[1]
    
            return score, {"criteria": criteria, "supporting_evidence": supporting_evidence}
    
    # Initialize the custom class
    prompt_with_conversation_relevence_custom = prompt_with_conversation_relevence()
    
    # Streamlit UI
    #st.title("LLM Evaluation Tool")
    st.write("Upload an Excel file with columns: Index, Question, Context, Answer, Reference Context, Reference Answer to evaluate relevance scores.")
    
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
    
            required_columns = ["Index", "Question", "Context", "Answer", "Reference Context", "Reference Answer"]
            if not all(col in df.columns for col in required_columns):
                st.error(f"The uploaded file must contain these columns: {', '.join(required_columns)}.")
            else:
                st.write("Preview of Uploaded Data:")
                st.dataframe(df.head())
    
                num_metrics = st.number_input("Enter the number of metrics you want to define:", min_value=1, step=1)
    
                # Initialize session state to store system prompts and results
                if "system_prompts" not in st.session_state:
                    st.session_state.system_prompts = {}
                if "combined_results" not in st.session_state:
                    st.session_state.combined_results = []
    
                for i in range(num_metrics):
                    # Insert a thick line and style the Metric header
                    st.markdown(f"""
                        <hr style="border: 5px solid #000000;">
                        <h3 style="background-color: #f0f0f0; padding: 10px; border: 2px solid #000000;">
                            Metric {i + 1}
                        </h3>
                    """, unsafe_allow_html=True)
    
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
                                    
                                    # Alternate between "Factual Correctness" and "Relevance"
                                    evaluation_type = "Factual Correctness" if (i + 1) % 2 == 0 else "Relevance"
                                    
                                    completion = openai.chat.completions.create(
                                        model="gpt-4",  # Correct model name
                                        messages=[
                                            {"role": "user", "content": (
                                                f"Generate a system prompt less than 200 tokens to evaluate {evaluation_type.lower()} "
                                                f"based on the following columns: {selected_column_names}. "
                                                f"Please provide a rating from 1 (not at all {evaluation_type.lower()}) to 10 (highly {evaluation_type.lower()})."
                                            )}
                                        ],
                                        max_tokens=200
                                    )
                                    system_prompt = completion.choices[0].message.content.strip()
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
    
                        valid_prompt = st.button(f"Validate Prompt for Metric {i + 1}", key=f"validate_{i}")
    
                        if valid_prompt:
                            selected_column_terms = {
                                col.lower().replace(" ", "_"): col
                                for col in selected_columns
                            }
                            errors = []
                            for term, original_column in selected_column_terms.items():
                                term_pattern = f"\\b{term.replace('_', ' ')}\\b"
                                if not re.search(term_pattern, system_prompt, re.IGNORECASE):
                                    errors.append(f"'{original_column}' needs to be included as '{term.replace('_', ' ')}' in the system prompt.")
    
                            if errors:
                                st.error(
                                    f"For Metric {i + 1}, the following errors were found in your system prompt: "
                                    f"{'; '.join(errors)}"
                                )
                            else:
                                st.success(f"System Prompt for Metric {i + 1} is valid.")
    
                    # Button for generating results for each metric
                    if st.button(f"Generate Results for Metric {i + 1}", key=f"generate_results_{i}"):
                        column_mapping = {
                            "Question": "question",
                            "Context": "formatted_context",
                            "Answer": "formatted_history",
                            "Reference Context": "formatted_reference_context",
                            "Reference Answer": "formatted_reference_answer"
                        }
                        results = []
                        for index, row in df.iterrows():
                            params = {"system_prompt": system_prompt}
                            for col in selected_columns:
                                if col in column_mapping:
                                    params[column_mapping[col]] = row[col]
    
                            score, details = prompt_with_conversation_relevence_custom.prompt_with_conversation_relevence_feedback(**params)
                            result_row = {
                                "Index": row["Index"],
                                "Metric": f"Metric {i + 1}",
                                "Selected Columns": ", ".join(selected_columns),
                                "Score": score,
                                "Criteria": details["criteria"],
                                "Supporting Evidence": details["supporting_evidence"],
                                "Question": row["Question"],
                                "Context": row["Context"],
                                "Answer": row["Answer"],
                                "Reference Context": row["Reference Context"],
                                "Reference Answer": row["Reference Answer"]
                            }
                            results.append(result_row)
                        st.session_state.combined_results.extend(results)
                        st.write(f"Results for Metric {i + 1}:")
                        st.dataframe(pd.DataFrame(results))
    
                # Button for generating combined results - only show if more than one metric is selected
                if num_metrics > 1 and st.button("Generate Overall Results"):
                    if st.session_state.combined_results:
                        st.write("Combined Results:")
                        st.dataframe(pd.DataFrame(st.session_state.combined_results))
                    else:
                        st.warning("No results to combine. Please generate results for individual metrics first.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    
    
    
    
    


















    # Add your Code 1 functionality here
elif st.session_state.active_page == "code2":
    # Full-Page Content for Code 2
    st.markdown('<div class="header-text"> Agentic CAI Testing </div>', unsafe_allow_html=True)
    #st.write("This is where Code 2 will execute.")
    #st.success("You are now viewing the full page for Code 2.")
    # Add your Code 2 functionality here

    import streamlit as st
    import pandas as pd
    import re
    import openai
    
    # Set OpenAI API keycompl
    
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
                User Input: {row['User Input']}
                Agent Prompt: {row['Agent Prompt']}
                Agent Response: {row['Agent Response']}
    
                Provide the following evaluation in this exact format:
    
                Criteria: [Provide the evaluation of the agent's response here]
                Supporting Evidence: [Provide supporting evidence for the evaluation here]
                Tool Triggered: [Identify any tools triggered here]
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
                st.write("GPT-4 Response:\n", response_content)
    
                # Validate and parse the response
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
    
                # Parse the structured response
                try:
                    for line in response_content.split("\n"):
                        line = line.strip()
                        if line.startswith("Criteria:"):
                            parsed_response["Criteria"] = line.replace("Criteria:", "").strip()
                        elif line.startswith("Supporting Evidence:"):
                            parsed_response["Supporting Evidence"] = line.replace("Supporting Evidence:", "").strip()
                        elif line.startswith("Tool Triggered:"):
                            parsed_response["Tool Triggered"] = line.replace("Tool Triggered:", "").strip()
                        elif line.startswith("Score:"):
                            parsed_response["Score"] = line.replace("Score:", "").strip()
                except Exception as e:
                    parsed_response["Criteria"] = "Error"
                    parsed_response["Supporting Evidence"] = f"Error parsing GPT-4 response: {e}"
                    parsed_response["Score"] = "N/A"
                    parsed_response["Tool Triggered"] = "N/A"
    
                # Append the parsed response
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
    #st.title("LLM Conversation Evaluation Tool")
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
                                    st.session_state.system_prompts[f"metric_{i}"] = system_prompt
                    
                                    # Automatic Validation
                                    system_prompt_lower = system_prompt.lower()
                                    missing_columns = [col for col in selected_columns if col.lower() not in system_prompt_lower]
                                    if missing_columns:
                                        st.warning(f"Validation failed! The system prompt is missing these columns: {', '.join(missing_columns)}.")
                                    else:
                                        st.success("Validation successful! All selected columns are included in the system prompt.")
                    
                                except Exception as e:
                                    st.error(f"Error generating or processing system prompt: {e}")
                    
                            system_prompt = st.session_state.system_prompts.get(f"metric_{i}", "")
                            st.text_area(
                                f"Generated System Prompt for Metric {i + 1}:", value=system_prompt, height=200
                            )
                    else:
                        system_prompt = st.text_area(
                            f"Enter the System Prompt for Metric {i + 1}:",
                            height=200
                        )
                    
                        # Add Validation Button
                        if st.button(f"Validate System Prompt for Metric {i + 1}", key=f"validate_prompt_{i}"):
                            if len(selected_columns) < 1:
                                st.error("Please select at least one column to validate against.")
                            else:
                                system_prompt_lower = system_prompt.lower()
                                missing_columns = [col for col in selected_columns if col.lower() not in system_prompt_lower]
                                if missing_columns:
                                    st.error(f"Validation failed! The system prompt is missing these columns: {', '.join(missing_columns)}.")
                                else:
                                    st.success("Validation successful! All selected columns are included in the system prompt.")
    
    
    
    
                    # Generate results for each metric
                    if st.button(f"Generate Results for Metric {i + 1}", key=f"generate_results_{i}"):
                        if system_prompt.strip() == "":
                            st.error("Please enter a valid system prompt.")
                        elif len(selected_columns) == 1:
                            st.error("Please select minimum two columns.")
                        else:
                            st.write("Evaluating conversations. Please wait...")
                            
                            results = evaluate_conversation(system_prompt, selected_columns, df, f"Metric {i + 1}")
                            #st.write(results)
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
    
    
    
    
    
    
    
    
    
    
    



elif st.session_state.active_page == "exit":
    st.markdown(
        '<div class="section-box"><h2>🚪 Exiting Application</h2><p>Thank you for using the app!</p></div>',
        unsafe_allow_html=True
    )
