import csv
import os
import random
from mistral_wrapper_llama_cpp import LlamaMistralWrapper
import pandas as pd
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from CodeT5Wrapper import CodeT5Wrapper
from extract_diff import import_dataset
from src.StarCoderWrapper import StarCoderWrapper
from src.T5Wrapper import T5Wrapper
from src.mistral_wrapper import MistralWrapper

load_dotenv()


def call_model_sync(model, messages):
    """Call given model with given prompts."""
    llm = LLMS[model]
    return llm.invoke(messages) if model == "mistral" else llm.invoke(messages).content

def call_model_with_prompt(model,prompt):
    llm = LLMS[model]
    return llm.invoke(prompt)


def prepare_prompt(diff):
    return f"Summarize this git diff into a useful, 10 words commit message:\n\n{diff}\n\nCommit message:"

def preprocess_diff_prepare_prompt(diff):
    PROMPT_TEMPLATE = """Please provide a descriptive commit message for the following changes.
                       Change:
                       Used to be
                       {before}
                       Is now
                       {after}
                        """
    lines=diff.split('\n')
    before_lines=[]
    after_lines=[]
    for line in lines:
        if line.startswith('-') and not line.startswith('---'):
            before_lines.append(line[1:].strip())
        elif line.startswith('+') and not line.startswith('+++'):
            after_lines.append(line[1:].strip())
    before='\n'.join(before_lines)
    after='\n'.join(after_lines)
    prompt=PROMPT_TEMPLATE.format(before=before, after=after)
    print(f"Prompt : {prompt}")
    return prompt

def generate_commit_message(prompt,model_name):
    return call_model_with_prompt(model_name, prompt)


def process_dataset_llms(model_name, dataset, csv_writer):
    for item in dataset:
        diff = item['diff']
        print(diff)
        original_message = item['message']
        # cleaned_diff_prompt = preprocess_diff_prepare_prompt(diff)
        prepared_prompt=prepare_prompt(diff)
        commit_message=generate_commit_message(prepared_prompt,model_name)
        csv_writer.writerow([original_message, commit_message])

def process_dataset_mistral(model_name,dataset,csv_writer):
    for item in dataset:
        diff = item['diff']
        # print(diff)
        original_message = item['message']
        print(f"Original message : {original_message}")
        prompt=prepare_prompt(diff)
        commit_message=call_model_with_prompt(model_name, prompt)
        print(f"Commit message : {commit_message}")
        csv_writer.writerow([original_message,commit_message])


def process_dataset_chatbot(model_name, dataset, csv_writer):
    """Process the dataset and write results to the CSV file."""

    for item in dataset:
        diff = item['diff']
        original_message = item['message']
        message = [
            SystemMessage(content="Be a helpful assistant with knowledge of git message conventions."),
            HumanMessage(content=f"Summarize this git diff into a useful, 10 words commit message: {diff}. It is very important that you only provide the final output without any additional comments or remarks."),
        ]
        model_output = call_model_sync(model_name, message)
        csv_writer.writerow([original_message, model_output])


if __name__ == "__main__":
    print("Compiling LLMs")
    LLMS = {
        # 'deepinfra': ChatDeepInfra(model="databricks/dbrx-instruct", temperature=0),
        # 'codellama': ChatOllama(model="codellama", base_url="http://localhost:11434"),
        # 'codet5': CodeT5Wrapper(model_name="Salesforce/codet5-base"),
        # # 'starcoder2':StarCoderWrapper(model_name="bigcode/starcoder2-7b"),
        # 'starcoder2': StarCoderWrapper(model_name="bigcode/starcoder2-3b"),
        # 'flanbase':T5Wrapper(model_name="google-t5/t5-small"),
        'mistral':LlamaMistralWrapper()
    }
    print("Creating Output directory")
    # Create output directory
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    print("Separating datasets")
    # Load dataset
    train_dataset, validation_dataset, test_dataset = import_dataset("Maxscha/commitbench")
    print("Receiving model Names")
    model_name = input("Enter the model name: ")

    # Handle invalid input
    if model_name not in LLMS:
        print(f"Model {model_name} not found.")
        exit(1)

    # Prepare subset for specific models
    dataset_to_process = (
        train_dataset.select(random.sample(range(len(train_dataset)), 10))
        if model_name == "mistral" else train_dataset
    )

    # Write output to CSV
    output_file = os.path.join(output_dir, "output.csv")
    with open(output_file, mode="w", newline='', encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Original Message", "Model Output"])
        # if model_name !='flanbase':
        #    process_dataset_chatbot(model_name, dataset_to_process, csv_writer)
        if model_name == "mistral":
            process_dataset_mistral(model_name, dataset_to_process, csv_writer)
        else:
            process_dataset_llms(model_name, dataset_to_process, csv_writer)

    # Display CSV content
    print(pd.read_csv(output_file))
    del LLMS[model_name]
