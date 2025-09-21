# core/local_llm.py
import os
import json
import re
import subprocess
from datetime import datetime
from llama_cpp import Llama

# ================== LOCAL LLAMA CONFIG ==================
MODEL_REPO = "QuantFactory/Meta-Llama-3-8B-Instruct-GGUF"
MODEL_FILE = "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"
GPU_LAYERS = 20   # tune based on your GPU
MODEL_PATH = None

try:
    print("🧠 Initializing Local LLM...")
    LLM = Llama.from_pretrained(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
        n_gpu_layers=GPU_LAYERS,
        n_ctx=4096,
        verbose=False
    )
    print("✅ Local LLM Initialized Successfully.")
except Exception as e:
    print(f"❌ CRITICAL ERROR: Failed to initialize Local LLM: {e}")
    LLM = None

# ================== UTILS ==================
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
        print("⚠️ 'code' not found in PATH. Please install or add VS Code to PATH.")

def log_generation(prompt, folder_path):
    try:
        os.makedirs(BASE_OUTPUT_FOLDER, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"\n[{datetime.now()}] Prompt: {prompt}\n→ Folder: {folder_path}\n")
    except:
        pass

def get_local_llm_response(prompt: str, max_tokens=2000) -> str:
    if LLM is None:
        return "Local LLM not available."
    try:
        print(f"🗨️ Querying Local LLM with prompt: {prompt[:200]}...")
        system_prompt = "You are Hornet AI, a helpful local code generator. Respond ONLY in strict JSON when asked for project output."
        full_prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        )
        response = LLM(
            full_prompt,
            max_tokens=max_tokens,
            stop=["<|eot_id|>"],
            echo=False
        )
        response_text = response["choices"][0]["text"].strip()
        print("🤖 Local LLM Response received.")
        return response_text
    except Exception as e:
        print(f"❌ Error querying Local LLM: {e}")
        return "{}"

# ================== PROJECT GENERATOR ==================
def generate_code_project(prompt: str):
    print(f"🛠️ Generating frontend project for: {prompt}")

    full_prompt = f"""
You are a senior frontend developer assistant.

Generate a complete frontend-only project for:
"{prompt}"

✅ Only use HTML, CSS, and JavaScript.
❌ No backend frameworks.
✅ Return output strictly in JSON format:
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
❌ No explanations, no markdown, only JSON.
"""

    raw_response = get_local_llm_response(full_prompt, max_tokens=3000)

    # Clean JSON if extra text is around
    match = re.search(r"\{.*\}", raw_response, re.DOTALL)
    if not match:
        print("❌ No valid JSON detected from LLM response.")
        return
    json_text = match.group(0)

    try:
        data = json.loads(json_text)
    except Exception as e:
        print("❌ JSON parse error:", e)
        return

    project_name = sanitize_name(data.get("project_name", "untitled_project"))
    folder_path = os.path.join(BASE_OUTPUT_FOLDER, project_name)
    os.makedirs(folder_path, exist_ok=True)

    for file in data.get("files", []):
        rel_path = file["path"]
        content = file["content"]
        full_path = os.path.join(folder_path, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄 Created: {rel_path}")

    open_in_vscode(folder_path)
    log_generation(prompt, folder_path)
    print("✅ Project generation complete.")

if __name__ == "__main__":
    user_input = input("🗣️ What project do you want to generate? ")
    generate_code_project(user_input)
