import csv
from transformers import AutoTokenizer
from transformers import AutoModelForSeq2SeqLM


class CodeT5Wrapper:
    def __init__(self, model_name="Salesforce/codet5-base"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def invoke(self,messages):
        input_text = messages[-1].content
        inputs=self.tokenizer(input_text,return_tensors="pt",truncation=True,max_length=512)
        outputs=self.model.generate(inputs.input_ids, max_length=50,num_beams=5,early_stopping=True)
        return self.tokenizer.decode(outputs[0],skip_special_tokens=True)

