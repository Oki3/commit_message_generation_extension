from itertools import groupby
import pandas as pd

MODEL_NAME = {
    "codellama": "CodeLlama 6.7B",
    "mistral": "Mistral 7B",
    "phi3.5": "Phi3.5 3.8B",
}

class Table:
    df: pd.DataFrame

    def __init__(self, filename: str):
        self.df = pd.read_csv(filename)
        self.value = ""

    def style(self, i, key):
        val = self.df.iloc[i][key] * 100
        max_val = self.df[key].max() * 100

        return rf"\textbf{{{val:.2f}}}" if abs(val - max_val) < 1e-12 else f"{val:.2f}"

    def table_start(self, title: str, l: list[tuple[str, int]], c: list[tuple[str, int]], second_row: list[str] = []):
        self.value += r"\begin{table*}[ht]" + "\n"
        self.value += r"\centering" + "\n"
        self.value += rf"\caption{{{title}}}" + "\n"
        self.value += r"\label{tab:evaluation}" + "\n"

        l_size = sum([x[1] for x in l])
        c_size = sum([x[1] for x in c])

        self.value += rf"\begin{{tabular}}{{{'l' * l_size + 'c' * c_size}}}" + "\n"
        self.value += r"\toprule" + "\n"

        cmidrules = []

        index = 1

        for i, (name, size) in enumerate(l + c):
            if size == 1:
                self.value += name
            else:
                self.value += rf"\multicolumn{{{size}}}{{c}}{{{name}}}"
                cmidrules.append((index, index + size - 1))
            if i != len(l + c) - 1:
                self.value += " & "

            index += size

        self.value += r"\\" + "\n"
        
        self.value += " ".join([r"\cmidrule(lr){" + f"{x[0]}-{x[1]}" + "}" for x in cmidrules])

        if len(second_row) > 0:
            self.value += " & ".join(second_row)
            self.value += r"\\" + "\n"

        self.value += r"\midrule" + "\n"

    def table_end(self):
        self.value += r"\bottomrule" + "\n"
        self.value += r"\end{tabular}" + "\n"
        self.value += r"\end{table*}" + "\n"

    def generate_full_results(self):
        self.table_start(
            r"Evaluation of different models, average for each $prompt \times model$ at temperature $0.7$. (As percentage)", 
            [("Model", 1), ("Prompt", 1)],
            [("Generated (raw)", 3), ("Generated (cleaned)", 3)],
            ["", "", "BLEU", "METEOR", "ROUGE-L", "BLEU", "METEOR", "ROUGE-L"]
        )

        last_model = None

        for i in range(len(self.df)):
            item = self.df.iloc[i]
            model = item["model"]
            prompt = item["prompt"]
            temperature = item["temperature"]

            if temperature != 0.7:
                continue

            row = ""

            if model != last_model:
                if last_model is not None:
                    row += r"\midrule"

                row += rf"\multirow{3}{{*}}{{{MODEL_NAME[model]}}} "
                last_model = model

            row += f"& {prompt} & {self.style(i, 'bleu_mean')} & {self.style(i, 'meteor_mean')} & {self.style(i, 'rouge_l_mean')} & {self.style(i, 'cleaned_bleu_mean')} & {self.style(i, 'cleaned_meteor_mean')} & {self.style(i, 'cleaned_rouge_l_mean')} \\\\"

            self.value += row + "\n"

        self.table_end()

        return self.value
    
    def generate_length_results(self):
        self.table_start(
            r"Evaluation of mean response length for each $prompt \times model$ at temperature $0.7$. (As percentage)", 
            [("Model", 1), ("Prompt", 1)],
            [("True length", 1), ("Generated (raw) length", 1), ("Generated (cleaned) length", 1)]
        )

        last_model = None

        for i in range(len(self.df)):
            item = self.df.iloc[i]
            model = item["model"]
            prompt = item["prompt"]
            temperature = item["temperature"]

            if temperature != 0.7:
                continue

            row = ""

            if model != last_model:
                if last_model is not None:
                    row += r"\midrule"

                row += rf"\multirow{3}{{*}}{{{MODEL_NAME[model]}}} "
                last_model = model

            row += f"& {prompt} & {item['true_mean_length']:.2f} & {item['mean_length']:.2f} & {item['cleaned_mean_length']:.2f} \\\\"

            self.value += row + "\n"

        self.table_end()

        return self.value
    
    def generate_temperature_results(self):
        self.table_start(
            r"Evaluation of Mistral 7B with few-shot for different temperatures. (As percentage)",
            [("Temperature", 1)],
            [("Generated (raw)", 3), ("Generated (cleaned)", 3)],
            ["", "BLEU", "METEOR", "ROUGE-L", "BLEU", "METEOR", "ROUGE-L"]
        )

        for i in range(len(self.df)):
            item = self.df.iloc[i]
            model = item["model"]
            temperature = item["temperature"]

            if model != "mistral" or temperature not in [0.0, 0.25, 0.5, 0.75, 1.0]:
                continue

            row = f"{temperature} & {self.style(i, 'bleu_mean')} & {self.style(i, 'meteor_mean')} & {self.style(i, 'rouge_l_mean')} & {self.style(i, 'cleaned_bleu_mean')} & {self.style(i, 'cleaned_meteor_mean')} & {self.style(i, 'cleaned_rouge_l_mean')} \\\\"

            self.value += row + "\n"

        self.table_end()

        return self.value

if __name__ == "__main__":
    print(Table("evaluation_results.csv").generate_temperature_results())
