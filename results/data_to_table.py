import pandas as pd
from itertools import groupby

def split_model(s):
    """
    Splits a string like 'codellama_uncleaned' into
    ('codellama', 'uncleaned').
    """
    parts = s.rsplit('_', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        return s, ""

def csv_to_latex_table(csv_path: str):
    df = pd.read_csv(csv_path)
    # Split model into (base_model, approach)
    df['base_model'], df['approach'] = zip(*df['model'].apply(split_model))

    # Only keep rows whose approach is one of {uncleaned, cleaned, aggressive}
    df = df[df['approach'].isin(['uncleaned','cleaned','aggressive'])]

    # Group by (base_model, prompt)
    grouped = df.groupby(['base_model', 'prompt'])

    # We'll collect rows in the structure:
    # [base_model, prompt,
    #  u_bleu, u_meteor, u_rouge,
    #  c_bleu, c_meteor, c_rouge,
    #  a_bleu, a_meteor, a_rouge]
    table_rows = []

    for (base_model, prompt), group in grouped:
        # We try to find a row for each approach
        row_uncleaned = group[group['approach'] == 'uncleaned']
        row_cleaned   = group[group['approach'] == 'cleaned']
        row_aggressive= group[group['approach'] == 'aggressive']

        # Only proceed if all three exist
        if (not row_uncleaned.empty and 
            not row_cleaned.empty and 
            not row_aggressive.empty):
            
            u = row_uncleaned.iloc[0]
            c = row_cleaned.iloc[0]
            a = row_aggressive.iloc[0]

            table_rows.append([
                base_model,
                prompt,
                u['bleu'],     # u_bleu
                u['meteor'],   # u_meteor
                u['rouge_l'],  # u_rouge
                c['bleu'],     # c_bleu
                c['meteor'],   # c_meteor
                c['rouge_l'],  # c_rouge
                a['bleu'],     # a_bleu
                a['meteor'],   # a_meteor
                a['rouge_l'],  # a_rouge
            ])

    # Sort the table rows so that rows for each base_model come together
    table_rows.sort(key=lambda r: (r[0], r[1]))

    # -----------------------------------------------------------------
    # Find maximum values (multiplied by 100) for each of the 9 columns
    # that represent uncleaned, cleaned, and aggressive metrics.
    # Indices in table_rows:
    #   2= u_bleu, 3= u_meteor, 4= u_rouge
    #   5= c_bleu, 6= c_meteor, 7= c_rouge
    #   8= a_bleu, 9= a_meteor, 10= a_rouge

    u_bleu_vals   = [row[2]*100 for row in table_rows]
    u_meteor_vals = [row[3]*100 for row in table_rows]
    u_rouge_vals  = [row[4]*100 for row in table_rows]

    c_bleu_vals   = [row[5]*100 for row in table_rows]
    c_meteor_vals = [row[6]*100 for row in table_rows]
    c_rouge_vals  = [row[7]*100 for row in table_rows]

    a_bleu_vals   = [row[8]*100  for row in table_rows]
    a_meteor_vals = [row[9]*100  for row in table_rows]
    a_rouge_vals  = [row[10]*100 for row in table_rows]

    max_u_bleu    = max(u_bleu_vals)   if u_bleu_vals   else 0
    max_u_meteor  = max(u_meteor_vals) if u_meteor_vals else 0
    max_u_rouge   = max(u_rouge_vals)  if u_rouge_vals  else 0

    max_c_bleu    = max(c_bleu_vals)   if c_bleu_vals   else 0
    max_c_meteor  = max(c_meteor_vals) if c_meteor_vals else 0
    max_c_rouge   = max(c_rouge_vals)  if c_rouge_vals  else 0

    max_a_bleu    = max(a_bleu_vals)   if a_bleu_vals   else 0
    max_a_meteor  = max(a_meteor_vals) if a_meteor_vals else 0
    max_a_rouge   = max(a_rouge_vals)  if a_rouge_vals  else 0

    # Helper function: if val is the maximum, we bold it
    def bold_if_max(val, max_val):
        # val and max_val are in "multiplied by 100" scale
        if abs(val - max_val) < 1e-12:
            return rf"\textbf{{{val:.2f}}}"
        else:
            return f"{val:.2f}"

    # -----------------------------------------------------------------
    # Produce LaTeX
    print(r"\begin{table*}[ht]")
    print(r"\centering")
    # We have: Model, Prompt, then 3 columns for Uncleaned,
    # 3 columns for Cleaned, and 3 columns for Aggressive => 11 columns total.
    # We'll define: l l ccc ccc ccc
    print(r"\begin{tabular}{llccccccccc}")
    print(r"\toprule")
    print(r"Model & Prompt & \multicolumn{3}{c}{Raw generated} & \multicolumn{3}{c}{Cleaned}\\")
    print(r"\cmidrule(lr){3-5} \cmidrule(lr){6-8}")
    print(r"& & BLEU & METEOR & ROUGE-L & BLEU & METEOR & ROUGE-L \\")
    print(r"\midrule")

    # Group again by base_model to print each group together
    first_model = True
    for base_model, rows in groupby(table_rows, key=lambda r: r[0]):
        # Convert the groupby object to a list (all rows for this base_model)
        rows = list(rows)
        n_rows = len(rows)
        first_row = True
        
        model_name = {
            "codellama": "CodeLLama 6.7B",
            "mistral": "Mistral 7B",
            "phi3.5": "Phi3.5 3.8B",
		}

        # If we want a horizontal line between each model group
        # but not above the first one, we can do:
        if not first_model:
            print(r"\midrule")
        first_model = False

        for row in rows:
            # row = [
            #   base_model, prompt,
            #   u_bleu, u_meteor, u_rouge,
            #   c_bleu, c_meteor, c_rouge,
            #   a_bleu, a_meteor, a_rouge
            # ]
            _, prompt, u_bleu, u_meteor, u_rouge, c_bleu, c_meteor, c_rouge, a_bleu, a_meteor, a_rouge = row

            # Multiply each value by 100
            u_bleu_100   = u_bleu*100
            u_meteor_100 = u_meteor*100
            u_rouge_100  = u_rouge*100

            c_bleu_100   = c_bleu*100
            c_meteor_100 = c_meteor*100
            c_rouge_100  = c_rouge*100

            a_bleu_100   = a_bleu*100
            a_meteor_100 = a_meteor*100
            a_rouge_100  = a_rouge*100

            # Possibly bold the top value in each column
            u_bleu_str   = bold_if_max(u_bleu_100, max_u_bleu)
            u_meteor_str = bold_if_max(u_meteor_100, max_u_meteor)
            u_rouge_str  = bold_if_max(u_rouge_100, max_u_rouge)

            c_bleu_str   = bold_if_max(c_bleu_100, max_c_bleu)
            c_meteor_str = bold_if_max(c_meteor_100, max_c_meteor)
            c_rouge_str  = bold_if_max(c_rouge_100, max_c_rouge)

            a_bleu_str   = bold_if_max(a_bleu_100, max_a_bleu)
            a_meteor_str = bold_if_max(a_meteor_100, max_a_meteor)
            a_rouge_str  = bold_if_max(a_rouge_100, max_a_rouge)

            if first_row:
                # Print the multirow for the model on the first row
                print(
                    rf"\multirow{{{n_rows}}}{{*}}{{{model_name[base_model]}}} & {prompt} & "
                    rf"{u_bleu_str} & {u_meteor_str} & {u_rouge_str} & "
                    rf"{c_bleu_str} & {c_meteor_str} & {c_rouge_str} \\"
                )
                first_row = False
            else:
                # Skip the first column (already multi-row) for subsequent lines
                print(
                    rf"& {prompt} & "
                    rf"{u_bleu_str} & {u_meteor_str} & {u_rouge_str} & "
                    rf"{c_bleu_str} & {c_meteor_str} & {c_rouge_str} \\"
                )

    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\caption{Evaluation of different models.}")
    print(r"\label{tab:evaluation}")
    print(r"\end{table*}")


if __name__ == "__main__":
    csv_file = "evaluation_results.csv"
    csv_to_latex_table(csv_file)
