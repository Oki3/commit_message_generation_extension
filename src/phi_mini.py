import torch
from accelerate import disk_offload
from llama_cpp import Llama

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig


class PhiMiniWrapper:
    def __init__(self):
        self.llm = Llama(
            model_path="/Users/nawminujhat/Desktop/Study Materials/ML for SE/team-3/llama.cpp/models/Phi-3.5-mini-instruct-Q8_0.gguf",
            n_ctx=2048,
            n_gpu_layers=48,
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