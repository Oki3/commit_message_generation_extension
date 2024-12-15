import pandas as pd
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from tabulate import tabulate

# file preprocessing
file_path = './output/output.csv'
df = pd.read_csv(file_path)

original_column = df.columns[0]
model_output_column = df.columns[1]

def compute_bleu(original, generated):
    """
    Compute BLEU score for a pair of texts (original and generated).
    Uses a smoothing function to handle short texts.
    """
    # tokenization
    original_tokens = original.split()
    generated_tokens = generated.split()
    smooth = SmoothingFunction().method4
    return sentence_bleu([original_tokens], generated_tokens, smoothing_function=smooth)


def evaluate_total_bleu(df):
    """
    Evaluate the total BLEU score as the average BLEU score across all rows.
    """
    total_score = 0
    for i, row in df.iterrows():
        original = str(row[original_column])
        model_output = str(row[model_output_column])
        total_score += compute_bleu(original, model_output)
    return total_score / len(df)

total_bleu = evaluate_total_bleu(df)

table = [["Total BLEU Score", total_bleu]]
print(tabulate(table, headers=["Metric", "Score"], tablefmt="grid"))
