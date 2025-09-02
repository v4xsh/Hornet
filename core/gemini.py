import google.generativeai as genai
import os

# --- LOAD PROJECT-SPECIFIC API KEY ---
# This looks for the key you set with the command above.
HORNET_API_KEY = os.getenv("HORNET_GEMINI_API_KEY")

if not HORNET_API_KEY:
    # This will stop the program if the key isn't set.
    raise ValueError("HORNET_GEMINI_API_KEY environment variable not found. Please run the 'set' command in your terminal before running the script.")

genai.configure(api_key=HORNET_API_KEY)

# Using a standard, high-performance model
gemini_model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def get_gemini_response(prompt):
    """
    Gets a response from the Gemini model.
    """
    try:
        response = gemini_model.generate_content(prompt)
        full_reply = response.text.strip()
        
        # A safer way to shorten the reply without causing errors
        if "." in full_reply:
            # Take the first sentence
            short_reply = full_reply.split(".")[0].replace("*", "") + "."
        else:
            # If no sentence, just take the first 300 characters
            short_reply = full_reply[:300].replace("*", "")

        return short_reply
        
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return "Sorry, I am having trouble connecting to my creative AI right now."