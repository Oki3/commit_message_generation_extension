# main_text.py

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import ollama
from pandas import DataFrame
import argparse
import time
import sys

#from post_processing.post_processing_csv import convert_to_result_file
#from post_processing.graphs import read_from_files_for_graphs
#from clean import clean_folder

# --------------------------------------------------------------------
# Model definitions
# --------------------------------------------------------------------
class Model:
    name: str = ""

    def run(self, prompt: str, temperature: float) -> str:
        response = ollama.generate(model=self.name, prompt=prompt, options={"temperature": temperature})
        return response.response

    def check_installed(self) -> bool:
        try:
            ollama.show(self.name)
            return True
        except:
            return False

class MistralModel(Model):
    name: str = "mistral"

# --------------------------------------------------------------------
# TxtExperiment (always Mistral, "fewshot")
# --------------------------------------------------------------------
class TxtExperiment:
    model: Model
    process_amount: int
    prompt: str
    # txt_file: str
    output_csv: str
    output_txt: str
    input_df: DataFrame | None = None
    output_df: DataFrame | None = None
    start_time: float = 0
    workers: int
    temperature: float

    def __init__(
        self,
        # txt_file: str,
        output_csv: str,
        output_txt: str,
        process_amount: int,
        workers: int,
        temperature: float
    ):
        self.model = MistralModel()
        self.prompt = "fewshot"
        
        # self.txt_file = txt_file
        self.output_csv = output_csv
        self.output_txt = output_txt
        self.process_amount = process_amount
        self.workers = workers
        self.temperature = temperature

        # We'll store the input lines in a DataFrame column "prompt"
        self.output_df = DataFrame(columns=["prompt", "generated_message"])

    def check_installed(self):
        if not self.model.check_installed():
            raise Exception(f"Model {self.model.name} is not installed.")

    def read_input(self):
        # """Read from a single .txt file, one prompt per line."""
        # if not os.path.exists(self.txt_file):
        #     raise FileNotFoundError(f"TXT file not found: {self.txt_file}")

        # print(f"Reading TXT: {self.txt_file}")
        # with open(self.txt_file, "r", encoding="utf-8") as f:
        #     lines = [l.strip() for l in f if l.strip()]

        # self.input_df = DataFrame({"prompt": lines})

        # # If the requested process_amount > number of lines, clamp it.
        # if self.process_amount > len(lines):
        #     self.process_amount = len(lines)
        # print("Reading from stdin...")
        self.output_df = DataFrame(columns=["prompt", "generated_message"])
        print("Reading from stdin...", file=sys.stderr)
        diff_content = sys.stdin.read()
        # print(f"Diff content read: {diff_content}")

        # Possibly split into lines or treat as one prompt
        lines = [diff_content]
        self.input_df = DataFrame({"prompt": lines})
        self.process_amount = len(lines)


    def save_output_csv(self):
        """Saves all columns (prompt and generated_message) to a CSV file."""
        with open(self.output_csv, "w", encoding="utf-8") as f:
         self.output_df.to_csv(f, index=False)

    def save_output_txt(self):
        """Saves only the generated messages to a .txt file (one per line)."""
        with open(self.output_txt, "w", encoding="utf-8") as f:
            for idx in range(len(self.output_df)):
                msg = self.output_df.loc[idx, "generated_message"]
                # In case of NaN or empty
                if not isinstance(msg, str):
                    msg = ""
                f.write(msg + "\n")


    def process_item(self, index: int, temperature: float) -> dict:
        item = self.input_df.iloc[index]
        prompt_line = item["prompt"]
        # Generate the commit message using the few-shot prompt
        generated_message = self.model.run(prompt_line, temperature)
        return {
            "prompt": prompt_line,
            "generated_message": generated_message
        }

    def print_progress(self, completed: int, total: int):
        time_elapsed = time.time() - self.start_time
        if completed > 0:
            time_remaining = (time_elapsed / completed) * (total - completed)
        else:
            time_remaining = 0
        print(
            f"Progress: {completed}/{total} "
            f"({(completed/total)*100:.2f}%) done. "
            f"Elapsed {time_elapsed:.2f}s, remaining: {time_remaining:.2f}s",file=sys.stderr
        )

    def append_result(self, index: int, result: dict):
        self.output_df.loc[index] = [
            result["prompt"],
            result["generated_message"]
        ]

    def append_error(self, index: int):
        item = self.input_df.iloc[index]
        self.output_df.loc[index] = [item["prompt"], ""]

    def start(self):
        self.start_time = time.time()

    def run_parallel(self):
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self.process_item, i, self.temperature): i
                for i in range(self.process_amount)
            }
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
        """Sequential version."""
        self.start()
        for i in range(self.process_amount):
            try:
                result = self.process_item(i, self.temperature)
                self.append_result(i, result)
                self.print_progress(i+1, self.process_amount)
            except Exception as e:
                print(f"Error processing item {i}: {e}")
                self.append_error(i)

parser = argparse.ArgumentParser(description="TXT-based experiment (always uses Mistral fewshot).")

# parser.add_argument("--txt_file", type=str, required=True, help="Path to the .txt file (one prompt per line).")
parser.add_argument("--output_csv", type=str, default="output_txt.csv", help="Output CSV file for tabular data.")
parser.add_argument("--output_txt", type=str, default="output_txt.txt", help="Output text file with generated lines.")
parser.add_argument("--process_amount", type=int, default=1, help="Number of lines to process.")
parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers.")
parser.add_argument("--sequential", action="store_true", help="Run sequentially instead of parallel.")
parser.add_argument("--temperature", type=float, default=0.7, help="Model generation temperature.")

if __name__ == "__main__":
    args = parser.parse_args()
    open(args.output_csv, "w").close()  
    open(args.output_txt, "w").close()  
    experiment = TxtExperiment(
    #    txt_file=args.txt_file,
        output_csv=args.output_csv,
        output_txt=args.output_txt,
        process_amount=args.process_amount,
        workers=args.workers,
        temperature=args.temperature
    )

    experiment.check_installed()
    experiment.read_input()

    if args.sequential:
        experiment.run()
    else:
        experiment.run_parallel()

    # Write full table to CSV
    experiment.save_output_csv()
    # Write only generated messages to .txt
    experiment.save_output_txt()
    for msg in experiment.output_df["generated_message"]:
        if isinstance(msg, str) and msg.strip():
            print(msg)
