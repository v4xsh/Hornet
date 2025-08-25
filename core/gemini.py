import google.generativeai as genai
from core.text_to_speech import speak
from core.text_to_speech import stop_buffering

# Gemini API Setup
GEMINI_API_KEY = "AIzaSyAi3RFimnFMykgvNuQE9bf9pseEFVdp0zw"
genai.configure(api_key=GEMINI_API_KEY)

gemini_model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

def get_gemini_response(prompt):
    try:
        response = gemini_model.generate_content(prompt)
        full_reply = response.text.strip()
        short_reply = full_reply[:300].split(".")[0].replace("*", "") + "."
        stop_buffering()
        return short_reply
    except Exception as e:
        stop_buffering()
        print("Gemini Error:", e)
        return "Sorry, I couldn't think of a reply right now."
