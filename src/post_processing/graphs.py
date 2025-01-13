import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



def read_from_files_for_graphs(file_path='./results/evaluation_results.csv'):
    data=pd.read_csv(file_path)
    avg_scores=data.groupby(['model','prompt'])[['bleu', 'meteor', 'rouge_l', 'bertscore']].mean().reset_index()
    models=avg_scores['model'].unique()
    prompts=avg_scores['prompt'].unique()
    metrics=['bleu', 'meteor', 'rouge_l', 'bertscore']
    titles=['BLEU Score', 'METEOR Score', 'ROUGE-L Score', 'BERTScore']
    for metric,title in zip(metrics,titles):
        fig,ax=plt.subplots(figsize=(10,6))
        prompt_positions=np.arange(len(prompts))
        bar_width=0.2

        for i,model in enumerate(models):
            model_data=avg_scores[avg_scores['model']==model]
            scores=[model_data[model_data['prompt']==prompt][metric].values[0] for prompt in prompts]
            ax.bar(prompt_positions+i*bar_width,scores,bar_width, label=str(model).capitalize()  if isinstance(model, str) else model.capitalize())
        ax.set_xlabel('Prompt Types')
        ax.set_ylabel(f'{title}')
        ax.set_title(f'{title} for Models and Prompt Types')
        ax.set_xticks(prompt_positions+bar_width*(len(models)-1)/2)
        ax.set_xticklabels(prompts)
        ax.legend(title="Models")
        plt.tight_layout()
        save_path=os.path.join('results/graphs',f'{metric}_performance.png')
        plt.savefig(save_path)
        plt.close()