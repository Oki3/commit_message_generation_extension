import os

from dotenv import load_dotenv
from llama_cpp import Llama

# Load environment variables from a .env file
load_dotenv()

# Initializes the LlamaMistralWrapper class, loading the Llama model with the environment variables
class LlamaMistralWrapper:
    try:
            self.llm = Llama(
                model_path=os.environ['MODEL_PATH_MISTRAL'],
                chat_format="llama-2",
                n_ctx=int(os.environ['CONTEXT_WINDOW_FOR_MISTRAL']),
                n_gpu_layers=int(os.environ['GPU_LAYERS']),
                verbose=True
            )
            # Print confirmation of model loading
            print("Loaded Mistral")
    except KeyError as e:
            # Raise an exception if required environment variables are missing
            raise Exception(f"Missing environment variable: {e}")

    #  Ensures that the Llama model is properly closed when the object is destroyed.
    def __del__(self):
        if hasattr(self, 'llm'):
            del self.llm
    
    # Generates a response for a given prompt using the Mistral model and return the generated output text
    def invoke(self, prompt):
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates meaningful git commit messages."},
            {"role": "user", "content": prompt}
        ]
        # Print message indicating output generation
        print("Generating Outputs")
        output=self.llm.create_chat_completion(messages,max_tokens=1024)
        return output['choices'][0]['message']['content'].strip()
