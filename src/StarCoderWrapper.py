from sympy.physics.units import temperature
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, BitsAndBytesConfig, AutoModelForCausalLM


class StarCoderWrapper:
    def __init__(self, model_name="Salesforce/codet5-base"):
        self.quantization_config=BitsAndBytesConfig(load_in_8bit=True)# Load model directly
        self.tokenizer = AutoTokenizer.from_pretrained(model_name,quantization=self.quantization_config)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

    def invoke(self,prompt):
        inputs=self.tokenizer(prompt,return_tensors="pt",truncation=True,max_length=1024,padding=True)
        outputs=self.model.generate(inputs.input_ids, max_new_tokens=100, temperature=0.7,
                                    early_stopping=True)
        return self.tokenizer.decode(outputs[0],skip_special_tokens=True)