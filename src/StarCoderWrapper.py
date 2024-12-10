import torch

from transformers import AutoTokenizer,AutoModelForCausalLM

class StarCoderWrapper:
    def __init__(self, model_name):
        # self.quantization_config=BitsAndBytesConfig(load_in_8bit=True)# Load model directly
        self.tokenizer = AutoTokenizer.from_pretrained(model_name,force_download=True)
        self.model = AutoModelForCausalLM.from_pretrained(model_name,force_download=True)
        # Use gpu in place of mps if you have it
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        self.model=self.model.to(self.device)

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.model.config.eos_token_id
        print("Loaded StarCoder2")

    def invoke(self,prompt):
        inputs=self.tokenizer(prompt,return_tensors="pt",truncation=True,max_length=1024,padding=True).to(self.device)
        outputs=self.model.generate(inputs.input_ids, max_new_tokens=100, temperature=0.7,
                                    early_stopping=True)
        return self.tokenizer.decode(outputs[0],skip_special_tokens=True)