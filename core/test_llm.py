# core/test_llm.py
import time
from core.local_llm import get_local_llm_response

def run_test():
    print("--- Starting Local LLM Test ---")

    start_time = time.time()
    
    test_prompt = ""
    response = get_local_llm_response(test_prompt)
    
    end_time = time.time()
    
    print("\n--- Test Complete ---")
    print(f"\nPrompt: {test_prompt}")
    print(f"\nResponse: {response}")
    print(f"\nTime Taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    run_test()