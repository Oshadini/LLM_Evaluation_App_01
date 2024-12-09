from trulens_eval.feedback import Select, Feedback


def process_excel_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the uploaded data and performs Trulens evaluation on each row.
    Returns a DataFrame with results for visualization.
    """
    results = []
    for index, row in data.iterrows():
        context = row.get("Context", "")
        question = row.get("Question", "")
        answer = row.get("Answer", "")
        ref_context = row.get("Reference Content", "")
        ref_answer = row.get("Reference Answer", "")
        
        # Replace with proper 'get' syntax for Trulens lens handling
        f_feedback = Feedback(custom_feedback.custom_metric_score).on(
            answer=Select.RecordOutput.get(answer),
            question=Select.RecordInput.get(question),
            context=Select.RecordInput.get(context)
        )

        # Use TruChain to capture the evaluation logic
        tru_chain = TruChain(
            chain=f_feedback,
            app_id="trulens_eval_app"
        )
        
        with tru_chain as recording:
            result = tru_chain.invoke({
                "answer": answer,
                "context": context,
                "question": question
            })
            
        # Fetch Trulens evaluation feedback
        tru = Tru()
        records, feedback = tru.get_records_and_feedback(app_ids=[])

        # Store feedback and results
        for fb, fb_result in records.items():
            results.append({
                "Context": context,
                "Question": question,
                "Answer": answer,
                "Reference Context": ref_context,
                "Reference Answer": ref_answer,
                "Score": fb_result.result,
                "Reason": fb_result.calls[0].meta.get("reason", "No reason provided")
            })

    # Convert results into a DataFrame
    return pd.DataFrame(results)
