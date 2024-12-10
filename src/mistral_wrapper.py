import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


class MistralWrapper:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name,
                                                          low_cpu_mem_usage=True,
                                                          torch_dtype=torch.bfloat16,
                                                          device_map="auto")

    def invoke(self,prompt):
        print("Preparing input...")
        inputs=self.tokenizer.apply_chat_template(prompt,
                                                  return_tensors="pt",
                                                  return_dict=True,
                                                  add_generation_prompt=True)
        eos_token_id= self.tokenizer.eos_token_id
        if eos_token_id is None:
            eos_token_id=self.tokenizer.convert_tokens_to_ids("</s>")
        outputs=self.model.generate(**inputs,
                                    max_new_tokens=200,
                                    eos_token_id=eos_token_id,
                                    do_sample=False,
                                    early_stopping=True)
        return self.tokenizer.decode(outputs[0],skip_special_tokens=True)