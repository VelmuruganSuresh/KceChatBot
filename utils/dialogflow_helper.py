from google.cloud import dialogflow_v2 as dialogflow

def detect_intent_with_payload(project_id, session_id, text, language_code='en-US'):
    """
    Returns the full response object from a Dialogflow detect intent call,
    including text and payload.
    """
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    
    text_input = dialogflow.types.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.types.QueryInput(text=text_input)
    
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
        return response  # Return the entire response object
    except Exception as e:
        print(f"Error in Dialogflow API call: {e}")
        return None