import google.generativeai as genai

# ✅ Gemini API Configuration (make sure API key is valid)
genai.configure(api_key="AIzaSyDOdBeb_FUGpCdN_caakKaPtKvxC5xIgk0")

def generate_mail_content(user_description):
    """
    Generates a professional subject and body for an email based on the user-provided description.
    """
    prompt = f"""
    Generate a professional email in proper formatting based on the following instruction:

    Instruction:
    {user_description}

    The response should be clearly divided as:
    Subject: <subject line>
    Body: <complete body of the email in professional tone>
    """

    try:
        model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")  # ✅ correct model path
        response = model.generate_content(prompt)
        
        # ✅ Get plain text output
        content = response.text.strip()

        # ✅ Parse Subject and Body
        subject = ""
        body = ""

        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.lower().startswith("subject"):
                subject = line.split(":", 1)[1].strip()
            elif line.lower().startswith("body"):
                body = "\n".join(lines[i+1:]).strip()
                break

        return {
            "subject": subject,
            "body": body
        }

    except Exception as e:
        print("❌ Gemini Error:", e)
        return {
            "subject": "Failed to generate subject",
            "body": "Unable to generate mail content due to an API error."
        }
