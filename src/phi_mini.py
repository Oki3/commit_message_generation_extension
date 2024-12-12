import os

import torch
from accelerate import disk_offload
from dotenv import load_dotenv
from llama_cpp import Llama

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

load_dotenv()

class PhiMiniWrapper:
    def __init__(self):
        self.llm = Llama(
            model_path=os.environ['MODEL_PATH_PHI'],
            n_ctx=int(os.environ['CONTEXT_WINDOW_FOR_PHI']),
            n_gpu_layers=int(os.environ['GPU_LAYERS']),
            verbose=True)

    def __del__(self):
       self.close()

    def close(self):
        if hasattr(self, 'llm'):
            try:
                del self.llm
            except:
                pass
        self.llm = None

    print("Loaded Phi_-3.5-mini-instruct-Q8_0")

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
        print("Generating Outputs")
        output = self.llm(formatted_prompt, max_tokens=1024,stop=["<|end|>"])
        return output['choices'][0]['text'].strip()