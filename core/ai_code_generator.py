import os
import json
import subprocess
from datetime import datetime
import re
import google.generativeai as genai

# ✅ Gemini API Setup
GEMINI_API_KEY = "AIzaSyDQX_kQmY6fOJV541r1y51MfsVqOAvy4Ak"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")

# 📁 Output folders
BASE_OUTPUT_FOLDER = os.path.join(os.getcwd(), "ai_projects")
LOG_FILE = os.path.join(BASE_OUTPUT_FOLDER, "ai_code_gen_log.txt")

def sanitize_name(name):
    name = name.strip().lower().replace(" ", "_")
    return re.sub(r"[^\w\d_]", "", name)

def open_in_vscode(folder_path, open_new_window=True):
    args = ["code"]
    if open_new_window:
        args.append("--new-window")
    args.append(folder_path)
    try:
        subprocess.Popen(args)
        print(f"🚀 Opened VS Code at: {folder_path}")
    except FileNotFoundError:
        print("⚠️ 'code' not found in PATH. Trying fallback...")
        possible_paths = [
            os.path.expandvars(r"%LocalAppData%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft VS Code\Code.exe"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    fallback_args = [path]
                    if open_new_window:
                        fallback_args.append("--new-window")
                    fallback_args.append(folder_path)
                    subprocess.Popen(fallback_args)
                    print(f"🚀 Opened VS Code at: {folder_path}")
                    return
                except Exception as e:
                    print(f"❌ Failed to launch fallback VS Code: {e}")
        print("❌ VS Code not found. Please install or add to PATH.")

def log_generation(prompt, folder_path):
    try:
        os.makedirs(BASE_OUTPUT_FOLDER, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"\n[{datetime.now()}] Prompt: {prompt}\n→ Folder: {folder_path}\n")
    except:
        pass

def generate_code_project(prompt):
    print(f"🛠️ Generating frontend project for: {prompt}")

    full_prompt = f"""
You are a senior frontend web developer assistant.

Generate a complete frontend-only project make sure is fully functional on copy paste for:
\"{prompt}\"

✅ Only use HTML, CSS, and JavaScript.
❌ No backend frameworks like Flask, Django, or Node.js.
✅ No markdown. No explanation.
✅ Output must be valid JSON like:
{{
  "project_name": "simple_todo_web",
  "files": [
    {{
      "path": "index.html",
      "content": "<!DOCTYPE html>\\n<html>...</html>"
    }},
    {{
      "path": "static/style.css",
      "content": "body {{ ... }}"
    }},
    {{
      "path": "static/script.js",
      "content": "document.addEventListener(...)"
    }}
  ]
}}
"""

    try:
        chat = gemini_model.start_chat()
        stream = chat.send_message(full_prompt, stream=True)
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return

    print("📡 working on your project...\n")

    buffer = ""
    project_name = "untitled_project"
    folder_path = None
    created_paths = set()
    vs_code_opened = False

    for chunk in stream:
        if not hasattr(chunk, "text") or not chunk.text:
            continue

        text = chunk.text
        print(text, end="")  # for terminal visibility
        buffer += text

        # ✅ Try to extract project name early
        if '"project_name":' in buffer and project_name == "untitled_project":
            try:
                match = re.search(r'"project_name"\s*:\s*"([^"]+)"', buffer)
                if match:
                    project_name = sanitize_name(match.group(1))
                    folder_path = os.path.join(BASE_OUTPUT_FOLDER, project_name)
                    os.makedirs(folder_path, exist_ok=True)

                    if not vs_code_opened:
                        open_in_vscode(folder_path)
                        vs_code_opened = True
            except Exception as e:
                print(f"\n⚠️ Could not parse project_name yet: {e}")

        # 🧩 Try to extract and stream files live
        while '"path":' in buffer and '"content":' in buffer:
            try:
                match = re.search(
                    r'{\s*"path"\s*:\s*"([^"]+)",\s*"content"\s*:\s*"((?:[^"\\]|\\.)*)"\s*}',
                    buffer
                )
                if not match:
                    break

                rel_path = match.group(1)
                raw_content = match.group(2)
                content = bytes(raw_content, "utf-8").decode("unicode_escape")

                full_path = os.path.join(folder_path or BASE_OUTPUT_FOLDER, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                if full_path not in created_paths:
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"\n📄 Created live: {rel_path}")
                    created_paths.add(full_path)

                buffer = buffer[match.end():]  # remove processed part
            except Exception as e:
                print(f"\n⚠️ Waiting for more data: {e}")
                break

    if folder_path and os.path.exists(folder_path):
        log_generation(prompt, folder_path)
        print("✅ Project generation complete.")
    else:
        print("❌ Project generation failed or was incomplete.")

if __name__ == "__main__":
    user_input = input("🗣️ What project do you want to generate? ")
    generate_code_project(user_input)
