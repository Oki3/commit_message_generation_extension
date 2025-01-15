from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import ollama
from pandas import read_csv, DataFrame
import argparse
import time

from post_processing.post_processing import convert_to_result_file
from post_processing.graphs import read_from_files_for_graphs


# The base class for all the models providing common functionalities
class Model:
    name: str = ""

    # Generate a response based on the provided prompt and options
    def run(self, prompt: str, temperature: float) -> str:
        response = ollama.generate(model=self.name, prompt=prompt, options={"temperature": temperature})

        return response.response
    
    # This will check if the model is installed
    def check_installed(self) -> bool:
        try:
            ollama.show(self.name)

            return True
        except:
            return False
    
# Specific models implementations with predefined names   
class MistralModel(Model):
    name: str = "mistral"

class CodellamaModel(Model):
    name: str = "codellama"
    
class Phi35Model(Model):
    name: str = "phi3.5"

# Class representing an expirement with the given model
class Experiment:
    model: Model
    input_size: int
    process_amount: int
    prompt: str
    input_file: str
    output_file: str
    input_df: DataFrame|None = None
    output_df: DataFrame|None = None
    start_time: float = 0
    workers: int
    temperature: float

    def __init__(self, model: Model, input_size: int, process_amount: int, prompt: str, input_folder: str, output_folder: str, workers: int, temperature: float):
        self.model = model
        self.input_size = input_size
        self.process_amount = process_amount
        self.prompt = prompt
        self.workers = workers
        self.temperature = temperature
        self.input_file = f"{input_folder}/{model.name}_{input_size}_{prompt}.csv"
        self.output_file = f"{output_folder}/{model.name}_{process_amount}_{prompt}_{temperature}.csv"
        
        self.output_df = DataFrame(columns=["hash", "project", "true_message", "generated_message"])

        # Ensure the process amount does not exceed the input size
        if self.process_amount > self.input_size:
            self.process_amount = self.input_size

    # Check if the associated model is installed
    def check_installed(self):
        if not self.model.check_installed():
            raise Exception(f"Model {self.model.name} is not installed.")
        
    # Read input from the CSV file    
    def read_input(self):
        self.input_df = read_csv(self.input_file)

    # Save output to the ouput CSV file
    def save_output(self):
        self.output_df.to_csv(self.output_file, index=False)

    # Process a single item using the model
    def process_item(self, index: int, temperature: float) -> dict:
        item = self.input_df.iloc[index]
        prompt = item['prompt']

        # Generate a message using the model
        generated_message = self.model.run(prompt, temperature)

        return {
            "hash": item['hash'],
            "project": item['project'],
            "true_message": item['true_message'],
            "generated_message": generated_message
        }
    
    # Display progress of the experiment
    def print_progress(self, completed: int, total: int):
        time_elapsed = time.time() - self.start_time
        time_remaining = (time_elapsed / completed) * (total - completed)

        print(f"Progress: {completed}/{total} ({(completed/total)*100:.2f}%) done. Elapsed {time_elapsed:.2f}s, remaining: {time_remaining:.2f}s")

    
    def append_result(self, index: int, result: dict):
        self.output_df.loc[index] = [
            result['hash'],
            result['project'],
            result['true_message'],
            result['generated_message']
        ]

    def append_error(self, index: int):
        item = self.input_df.iloc[index]

        self.output_df.loc[index] = [
            item['hash'],
            item['project'],
            item['true_message'],
            ""
        ]

    def start(self):
        self.start_time = time.time()

    def run_parallel(self):
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.process_item, i, self.temperature): i for i in range(self.process_amount)}
            total = len(futures)
            completed = 0

            self.start()

            try:
                for future in as_completed(futures):
                    index = futures[future]

                    try:
                        result = future.result()
                        self.append_result(index, result)

                        completed += 1
                        self.print_progress(completed, total)
                    except Exception as e:
                        print(f"Error processing item {index}: {e}")
                        self.append_error(index)
            except KeyboardInterrupt:
                print("Interrupted")
                executor.shutdown(wait=False, cancel_futures=True)
                raise KeyboardInterrupt()

    def run(self):
        self.start()

        for i in range(self.process_amount):
            try:
                result = self.process_item(i, self.temperature)
                self.append_result(i, result)
                self.print_progress(i+1, self.process_amount)
            except Exception as e:
                print(f"Error processing item {i}: {e}")
                self.append_error(i)

MODELS = {
    "mistral": MistralModel(),
    "codellama": CodellamaModel(),
    "phi3.5": Phi35Model()
}
EXPERIMENTS = ["baseline", "fewshot", "cot"]

parser = argparse.ArgumentParser(description="Run one of the experiments with the specified model.")

parser.add_argument("--model", type=str, default="mistral", choices=MODELS.keys(), help="The model to use.")
parser.add_argument("--prompt", type=str, default="baseline", choices=EXPERIMENTS, help="The prompt to use.")
parser.add_argument("--input_size", type=int, default=1000, help="The size of the input.")
parser.add_argument("--process_amount", type=int, default=1000, help="The number of items to process.")
parser.add_argument("--sequential", action="store_true", help="Run the experiment sequentially instead of in parallel.")
parser.add_argument("--input_folder", type=str, default="./input", help="The folder containing the input files.")
parser.add_argument("--output_folder", type=str, default="./output", help="The folder to save the output files.")
parser.add_argument("--temperature", type=float, default=0.7, help="The temperature for the model generation.")
parser.add_argument("--workers", type=int, default=5, help="The number of workers to use for parallel processing.")
parser.add_argument("--get_result_file",action="store_true",help="Get the scores for obtained results")
parser.add_argument("--draw_graphs",action="store_true",help="Draw the graphs")

if __name__ == "__main__":
    args = parser.parse_args()
    if args.get_result_file:
        convert_to_result_file()
    if args.draw_graphs:
        read_from_files_for_graphs()
    else:

     model_name = args.model
     model = MODELS[model_name]
     prompt = args.prompt
     input_size = args.input_size
     process_amount = args.process_amount
     sequential = args.sequential
     input_folder = args.input_folder
     output_folder = args.output_folder
     temperature = args.temperature
     workers = args.workers

     os.makedirs(output_folder, exist_ok=True)

     experiment = Experiment(model, input_size, process_amount, prompt, input_folder, output_folder, workers, temperature)
     experiment.check_installed()
     experiment.read_input()

     if sequential:
        experiment.run()
     else:
        experiment.run_parallel()

     experiment.save_output()
     convert_to_result_file()