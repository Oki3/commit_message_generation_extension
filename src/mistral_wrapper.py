import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from accelerate import disk_offload

class MistralWrapper:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        print(self.device)
        self.model = AutoModelForCausalLM.from_pretrained(model_name,
                                                          low_cpu_mem_usage=True,
                                                          torch_dtype=torch.bfloat16,
                                                          device_map=self.device)

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.model.config.eos_token_id
        # self.model = self.model.to(self.device)
        disk_offload(self.model, offload_dir="offload")
        print("Loaded Mistral")

    def invoke(self,prompt):
        print("Preparing input...")
        inputs=self.tokenizer.apply_chat_template(prompt,
                                                  return_tensors='pt',
                                                  return_dict=True,
                                                  add_generation_prompt=True)
        inputs.to(self.device)
        outputs=self.model.generate(**inputs,max_new_tokens=1000)
        return self.tokenizer.decode(outputs[0],skip_special_tokens=True)