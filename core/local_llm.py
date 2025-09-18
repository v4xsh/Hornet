# core/local_llm.py

from llama_cpp import Llama
import os

# --- MODEL CONFIGURATION ---
# This will download the model to a local cache folder the first time you run it.
# You can choose different models from Hugging Face based on your needs.
MODEL_REPO = "QuantFactory/Meta-Llama-3-8B-Instruct-GGUF"
MODEL_FILE = "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"
MODEL_PATH = None # We will let the library handle the download path

# --- LLAMA CPP CONFIGURATION ---
# If you have a powerful GPU, you can offload more layers.
# -1 means offload all possible layers to the GPU.
# 0 means use CPU only.
GPU_LAYERS = 20 # A good starting point for a mid-range GPU. Set to 0 if you have no GPU.

try:
    print("🧠 Initializing Local LLM...")
    LLM = Llama.from_pretrained(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
        n_gpu_layers=GPU_LAYERS,
        n_ctx=2048, # Context window size
        verbose=False
    )
    print("✅ Local LLM Initialized Successfully.")
except Exception as e:
    print(f"❌ CRITICAL ERROR: Failed to initialize Local LLM: {e}")
    print("Please check your installation of llama-cpp-python and model details.")
    LLM = None

def get_local_llm_response(prompt: str, max_tokens=500) -> str:
    """
    Queries the local LLM and returns the response.
    """
    if LLM is None:
        return "Local LLM is not available due to an initialization error."

    try:
        print(f"🗨️  Querying Local LLM with prompt: {prompt}")
        
        # Create a structured prompt for better responses
        system_prompt = "You are Hornet AI, a helpful and concise voice assistant running locally on the user's machine."
        full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"

        response = LLM(
            full_prompt,
            max_tokens=max_tokens,
            stop=["<|eot_id|>"], # Stop generating at the end of the response
            echo=False # Don't echo the prompt back in the response
        )
        
        response_text = response['choices'][0]['text'].strip()
        print(f"🤖 Local LLM Response: {response_text}")
        return response_text
        
    except Exception as e:
        print(f"❌ Error querying Local LLM: {e}")
        return "I encountered an error while processing your request with my local AI."