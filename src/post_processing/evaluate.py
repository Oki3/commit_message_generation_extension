
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
from pandas import DataFrame
from rouge_score import rouge_scorer
from bert_score import score as bert_score
from nltk.tokenize import word_tokenize
from tabulate import tabulate
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt_tab')
nltk.download('wordnet')
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

# the first time running they need to be downloaded


# #File preprocessing
# file_path = './output/output.csv'
# df = pd.read_csv(file_path)
#
# original_column = df.columns[0]
# model_output_column = df.columns[1]


# BLEU Score
def compute_bleu(original, generated):
    """
    Compute BLEU score for a pair of texts (original and generated).
    Uses a smoothing function to handle short texts.
    """
    original_tokens = original.split()
    generated_tokens = generated.split()
    smooth = SmoothingFunction().method4
    return sentence_bleu([original_tokens], generated_tokens, smoothing_function=smooth)

# METEOR Score
def compute_meteor(original, generated):
    """Compute METEOR score for a pair of texts."""
    original_tokens = word_tokenize(original)  # Tokenize the original string
    generated_tokens = word_tokenize(generated)  # Tokenize the generated string
    return meteor_score([original_tokens], generated_tokens)

# ROUGE-L Score
def compute_rouge_l(original, generated):
    """Compute ROUGE-L score for a pair of texts."""
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(original, generated)
    return scores['rougeL'].fmeasure

# BERTScore
def compute_bertscore(originals, generated):
    """Compute BERTScore for the dataset."""
    P, R, F1 = bert_score(generated, originals, lang="en", rescale_with_baseline=False)
    return F1.mean().item()

# Evaluate metrics
def evaluate_metrics(df:DataFrame, original_column:str="true_message", model_output_column:str="generated_message"):
    total_bleu = 0
    total_meteor = 0
    total_rouge_l = 0

    originals = []
    generated = []

    for i, row in df.iterrows():
        original = str(row[original_column])
        model_output = str(row[model_output_column])

        originals.append(original)
        generated.append(model_output)

        total_bleu += compute_bleu(original, model_output)
        total_meteor += compute_meteor(original, model_output)
        total_rouge_l += compute_rouge_l(original, model_output)

    avg_bleu = total_bleu / len(df)
    avg_meteor = total_meteor / len(df)
    avg_rouge_l = total_rouge_l / len(df)

    #avg_bertscore = compute_bertscore(originals, generated)
    avg_bertscore = 0
    average_all_score=(avg_bleu+avg_meteor+avg_rouge_l+avg_bertscore)/4

    return avg_bleu, avg_meteor, avg_rouge_l, avg_bertscore,average_all_score

# Compute all metrics
def calculate_average_scores(df:DataFrame):
 avg_bleu, avg_meteor, avg_rouge_l, avg_bertscore,average_all_score = evaluate_metrics(df)

# Print results in a table
 results_table = [
    ["BLEU", avg_bleu],
    ["METEOR", avg_meteor],
    ["ROUGE-L", avg_rouge_l],
    ["BERTScore", avg_bertscore],
     ["AVERAGE SCORE", average_all_score]
 ]

 print(tabulate(results_table, headers=["Metric", "Score"], tablefmt="grid"))
