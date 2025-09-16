import google.generativeai as genai
import json

# Per your request, the API key is left as is.
genai.configure(api_key="AIzaSyDOdBeb_FUGpCdN_caakKaPtKvxC5xIgk0")

# ✅ 1. FUNCTION SIGNATURE UPDATED
def generate_mail_content(description, recipient_name, sender_name):
    """
    Generates a complete, professional email using Gemini,
    including a proper salutation and closing.
    """
    # ✅ 2. A BETTER, MORE DETAILED PROMPT
    # This prompt asks the AI to act as an assistant and create the entire email.
    # It also requests the output in a structured JSON format for reliability.
    prompt = f"""
        You are a professional email writing assistant. Your task is to compose a complete email.
        The user wants to send an email about the following topic: "{description}".
        
        The email is being sent to a person named: "{recipient_name}".
        The email is from a person named: "{sender_name}".
        
        Generate a JSON object with two keys: "subject" and "body".
        - The "subject" should be a concise and professional subject line.
        - The "body" must be the complete email content, including a professional salutation (e.g., "Dear {recipient_name},") and a professional closing (e.g., "Best regards,\\n{sender_name}").
        
        Do not include any extra text or explanations outside of the JSON object.
    """

    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        # ✅ 3. MORE RELIABLE JSON PARSING
        # This cleans up the AI's response and loads it as a structured object.
        json_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        email_data = json.loads(json_response_text)
        
        return email_data

    except Exception as e:
        print(f"❌ Gemini Mail Generation Error: {e}")
        # Return a dictionary with an error message to prevent crashes
        return {"subject": "Error", "body": "Failed to generate email content."}
