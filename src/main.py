from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import ollama
from pandas import read_csv, DataFrame
import argparse

class Model:
    name: str = ""

    def run(self, prompt: str) -> str:
        response = ollama.chat(model=self.name, messages=[{
            "role": "user",
            "content": prompt
        }])

        return response.message.content.strip()
    
    def check_installed(self) -> bool:
        try:
            ollama.show(self.name)

            return True
        except:
            return False
    
class MistralModel(Model):
    name: str = "mistral"

    def run(self, prompt: str) -> str:
        return super().run(prompt)

class CodellamaModel(Model):
    name: str = "codellama"

    def run(self, prompt: str) -> str:
        return super().run(prompt)
    
class Phi35Model(Model):
    name: str = "phi3.5"

    def run(self, prompt: str) -> str:
        return super().run(prompt)

MODELS = {
    "mistral": MistralModel(),
    "codellama": CodellamaModel(),
    "phi3.5": Phi35Model()
}
EXPERIMENTS = ["baseline", "few_shot", "cot"]
INPUT_FOLDER = './input'
OUTPUT_FOLDER = './output'

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

parser = argparse.ArgumentParser(description="Run a model with a given prompt.")

parser.add_argument("--model", type=str, default="mistral", choices=MODELS.keys(), help="The model to use.")
parser.add_argument("--prompt", type=str, default="baseline", choices=EXPERIMENTS, help="The prompt to use.")
parser.add_argument("--size", type=int, default=1000, help="The number of items to process.")

class Experiment:
    model: Model
    size: int
    prompt: str
    input_file: str
    output_file: str
    input_df: DataFrame|None = None
    output_df: DataFrame|None = None

    def __init__(self, model: Model, size: int, prompt: str, folder: str):
        self.model = model
        self.size = size
        self.prompt = prompt
        self.input_file = f"{folder}/{model.name}_{1000}_{prompt}.csv"
        self.output_file = f"{OUTPUT_FOLDER}/{model.name}_{size}_{prompt}.csv"

    def check_installed(self):
        if not self.model.check_installed():
            raise Exception(f"Model {self.model.name} is not installed.")
        
    def read_input(self):
        self.input_df = read_csv(self.input_file)

    def save_output(self):
        self.output_df.to_csv(self.output_file, index=False)

    def process_item(self, index: int):
        item = self.input_df.iloc[index]
        prompt = item['prompt']

        print(f"{self.model.name}/{self.prompt} - {item['hash'][:7]} - running")

        generated_message = self.model.run(prompt)

        print(f"{self.model.name}/{self.prompt} - {item['hash'][:7]} - finished")

        return {
            "hash": item['hash'],
            "project": item['project'],
            "true_message": item['true_message'],
            "generated_message": generated_message
        }

    def run(self):
        self.output_df = DataFrame(columns=["hash", "project", "true_message", "generated_message"])

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.process_item, i): i for i in range(self.size)}
            total = len(futures)
            completed = 0

            for future in as_completed(futures):
                index = futures[future]
                try:
                    result = future.result()
                    self.output_df.loc[index] = [
                        result['hash'],
                        result['project'],
                        result['true_message'],
                        result['generated_message']
                    ]
                    completed += 1
                    print(f"Progress: {completed}/{total} ({(completed/total)*100:.2f}%) done")
                except Exception as e:
                    print(f"Error processing item {index}: {e}")

if __name__ == "__main__":
    args = parser.parse_args()

    model_name = args.model
    model = MODELS[model_name]
    prompt = args.prompt
    size = args.size

    experiment = Experiment(model, size, prompt, INPUT_FOLDER)
    experiment.check_installed()
    experiment.read_input()
    experiment.run()
    experiment.save_output()