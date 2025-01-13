import pandas as pd
from itertools import groupby

def parse_model_approach(s: str):
    parts = s.rsplit('_', 1)
    return parts[0], parts[1] if len(parts) == 2 else ("", "")

def read_and_filter_csv(csv_path: str):
    df = pd.read_csv(csv_path)
    df['base_model'], df['approach'] = zip(*df['model'].apply(parse_model_approach))
    df = df[df['approach'].isin(['uncleaned','cleaned','aggressive'])]
    return df

def group_and_organize(df: pd.DataFrame):
    grouped = df.groupby(['base_model', 'prompt'])
    rows = []
    for (base_model, prompt), group in grouped:
        row_u = group[group['approach'] == 'uncleaned']
        row_c = group[group['approach'] == 'cleaned']
        row_a = group[group['approach'] == 'aggressive']
        if not (row_u.empty or row_c.empty or row_a.empty):
            u, c, a = row_u.iloc[0], row_c.iloc[0], row_a.iloc[0]
            rows.append([
                base_model,
                prompt,
                u['bleu'], u['meteor'], u['rouge_l'],
                c['bleu'], c['meteor'], c['rouge_l'],
                a['bleu'], a['meteor'], a['rouge_l'],
            ])
    rows.sort(key=lambda r: (r[0], r[1]))
    return rows

def compute_max_values(rows):
    all_vals = [ [r[idx]*100 for r in rows] for idx in range(2,11) ]
    
    return [max(vals) if vals else 0 for vals in all_vals]

def bold_if_max(val: float, max_val: float):
    return rf"\textbf{{{val:.2f}}}" if abs(val - max_val) < 1e-12 else f"{val:.2f}"

def generate_latex(table_rows):
    maxima = compute_max_values(table_rows)
    model_name = {
        "codellama": "CodeLLama 6.7B",
        "mistral": "Mistral 7B",
        "phi3.5": "Phi3.5 3.8B",
    }

    print(r"\begin{table*}[ht]")
    print(r"\centering")
    print(r"\begin{tabular}{llccccccccc}")
    print(r"\toprule")
    print(r"Model & Prompt & \multicolumn{3}{c}{Generated (raw)} & \multicolumn{3}{c}{Generated (cleaned)}\\")
    print(r"\cmidrule(lr){3-5} \cmidrule(lr){6-8}")
    print(r"& & BLEU & METEOR & ROUGE-L & BLEU & METEOR & ROUGE-L \\")
    print(r"\midrule")

    first_model = True
    for base_model, rows in groupby(table_rows, key=lambda r: r[0]):
        rows = list(rows)
        if not first_model: print(r"\midrule")
        first_model = False

        for i, row in enumerate(rows):
            _, prompt, *vals = row
            # u_bleu, u_meteor, u_rouge, c_bleu, c_meteor, c_rouge, a_bleu, a_meteor, a_rouge
            bolded_vals = [
                bold_if_max(vals[j]*100, maxima[ j ]) 
                for j in range(9)
            ]
            if i == 0:
                print(
                    rf"\multirow{{{len(rows)}}}{{*}}{{{model_name.get(base_model, base_model)}}} & {prompt} & "
                    + f"{bolded_vals[0]} & {bolded_vals[1]} & {bolded_vals[2]} & "
                    + f"{bolded_vals[3]} & {bolded_vals[4]} & {bolded_vals[5]} \\\\"
                )
            else:
                print(
                    rf"& {prompt} & {bolded_vals[0]} & {bolded_vals[1]} & {bolded_vals[2]} & "
                    + f"{bolded_vals[3]} & {bolded_vals[4]} & {bolded_vals[5]} \\\\"
                )

    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\caption{Evaluation of different models.}")
    print(r"\label{tab:evaluation}")
    print(r"\end{table*}")

def csv_to_latex_table(csv_path: str):
    df = read_and_filter_csv(csv_path)
    table_rows = group_and_organize(df)
    generate_latex(table_rows)

if __name__ == "__main__":
    csv_to_latex_table("evaluation_results.csv")
