from linecache import cache

from langchain.chains.question_answering.map_reduce_prompt import messages
from llama_cpp import Llama

class LlamaMistralWrapper:

    def __init__(self):
         self.llm=Llama(model_path="/Users/nawminujhat/Desktop/Study Materials/ML for SE/team-3/llama.cpp/models/mistral-7b-instruct-v0.2.Q6_K.gguf",
                        chat_format="llama-2",
                        n_ctx=2048,
                        verbose=True)

    def __del__(self):
        if hasattr(self, 'llm'):
            del self.llm
    print("Loaded Mistral")
    def invoke(self, prompt):
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates meaningful git commit messages."},
            {"role": "user", "content": prompt}
        ]
        print("Generating Outputs")
        output=self.llm.create_chat_completion(messages,max_tokens=1024)
        return output['choices'][0]['message']['content'].strip()
