from core.mail_assistant import clean_username, replace_placeholders
import re

# Mock inputs for testing
username_raw = "vansh dobhal"
description = "I am unable to attend class tomorrow as I will be representing our college in a football match."

# Step 1: clean username
username = clean_username(username_raw)
to_email = username + "@gmail.com"

# Step 2: mock recipient name extraction
recipient_name = "Teacher"
sender_name = "Vansh"

# Step 3: simulate LLM draft (normally returned by LLM)
llm_response = {
    "subject": "Creating a professional mail: Request for Exemption from Tomorrow's Class",
    "body": """Dear After,

I am writing to request a temporary exemption from tomorrow's class as I will be representing our college in a football match. As a result, I will be unavailable for the class and will need to catch up on the material at a later date.

I would greatly appreciate it if you could grant me this exemption. I will make sure to complete all my assignments and stay on top of my coursework despite missing the class.

Thank you for your understanding and support.

Best regards,
Hornet"""
}

# Step 4: clean subject
subject = re.sub(r"(?i)creating a professional mail|professional email for .*", "", llm_response["subject"]).strip()
if not subject:
    subject = "No Subject"

# Step 5: clean body placeholders
body = llm_response["body"]
body = replace_placeholders(body, recipient_name, sender_name)
body = re.sub(r"\bAfter\b", recipient_name, body)
body = re.sub(r"\bYour Name\b", sender_name, body)

if not re.search(r"(best regards|thanks|sincerely)", body.lower()):
    body += f"\n\nBest regards,\n{sender_name}"

# Step 6: ensure proper paragraph spacing
body = "\n\n".join([line.strip() for line in body.split("\n") if line.strip()])

# Step 7: print results for testing
print("=== TEST EMAIL ===")
print("To:", to_email)
print("Subject:", subject)
print("Body:\n", body)
