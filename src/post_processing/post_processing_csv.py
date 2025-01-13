import os
import pandas as pd

from .evaluate import (evaluate_metrics)

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

def read_and_evaluate_files(output_dir='./output'):
    results = {
        'model':[],
        'prompt':[],
        'bleu':[],
        'meteor':[],
        'rouge_l':[],
        'bertscore':[]
    }
    for filename in os.listdir(output_dir):
        if filename.endswith('.csv'):
            parts=filename.replace('.csv','').split('_')
            model=parts[0]
            prompt_type=parts[2]
            df=pd.read_csv(os.path.join(output_dir,filename),usecols=['true_message','generated_message'])
            bleu,meteor,rouge_l,bertscore,average_all_score=evaluate_metrics(df)
            results['model'].append(model)
            results['prompt'].append(prompt_type)
            results['bleu'].append(bleu)
            results['meteor'].append(meteor)
            results['rouge_l'].append(rouge_l)
            results['bertscore'].append(bertscore)
            print(results)
    return pd.DataFrame(results)

def convert_to_result_file():
    results_df=read_and_evaluate_files()
    results_df.to_csv('./results/evaluation_results.csv',index=False)
    print(results_df.to_string())


