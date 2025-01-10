import os

from dotenv import load_dotenv
from llama_cpp import Llama

# Load environment variables from a .env file
load_dotenv()

# Initializes the PhiMiniWrapper class, loading the Llama model with settings from environment variables.
class PhiMiniWrapper:
    def __init__(self):
        try:
            self.llm = Llama(
                model_path=os.environ['MODEL_PATH_PHI'],
                n_ctx=int(os.environ['CONTEXT_WINDOW_FOR_PHI']),
                n_gpu_layers=int(os.environ['GPU_LAYERS']),
                verbose=True
            )
            # Print confirmation of model loading
            print("Loaded Phi_-3.5-mini-instruct-Q8_0")
        except KeyError as e:
            # Raise an exception if required environment variables are missing
            raise Exception(f"Missing environment variable: {e}")

    # Ensures that the Llama model is properly closed when the object is destroyed
    def __del__(self):
       self.close()

    # Closes the Llama model and releases any associated resources
    def close(self):
        if hasattr(self, 'llm'):
            try:
                del self.llm
            except Exception as e:
                # Print an error message if closing the model fails
                print(f"Error while closing the model: {e}")
        self.llm = None

    # Generates a response for a given prompt using the Llama model and return the generated output text
    def invoke(self, prompt):
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates meaningful git commit messages."},
            {"role": "user", "content": prompt}
        ]
        formatted_prompt = (
            "<|system|>\n"
            f"{messages[0]['content']}<|end|>\n"
            "<|user|>\n"
            f"{messages[1]['content']}<|end|>\n"
            "<|assistant|>\n"
        )
        # Print message indicating output generation
        print("Generating Outputs")
        output = self.llm(formatted_prompt, max_tokens=1024,stop=["<|end|>"])
        return output['choices'][0]['text'].strip()