import csv
import os
import random
import time

from mistral_wrapper_llama_cpp import LlamaMistralWrapper
import pandas as pd
from dotenv import load_dotenv
from langchain_community.chat_models import ChatDeepInfra
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from extract_diff import import_dataset
from phi_mini import PhiMiniWrapper

load_dotenv()


def call_model_sync(model, messages):
    """Call given model with given prompts."""
    llm = LLMS[model]
    return llm.invoke(messages) if model == "mistral" else llm.invoke(messages).content


def call_model_with_prompt(model, prompt):
    llm = LLMS[model]
    return llm.invoke(prompt)


def prepare_prompt(diff, model_name):
    if model_name == 'mistral':
        return f"Summarize this git diff into a useful, 10 words commit message{diff}\n\nCommit message:"
    elif model_name == 'phi_mini':
        return (f"Summarize this git diff into a useful, 10 words commit message{diff}. "
                f"You should only output the commit message and no extra description.\n\nCommit message:")


def generate_commit_message(prompt, model_name):
    return call_model_with_prompt(model_name, prompt)


def process_dataset_quantized_instruct(model_name, dataset, csv_writer):
    for item in dataset:
        diff = item['diff']
        # print(diff)
        original_message = item['message']
        print(f"Original message : {original_message}")
        prompt = prepare_prompt(diff, model_name)
        commit_message = generate_commit_message(prompt, model_name)
        print(f"Commit message : {commit_message}")
        csv_writer.writerow([original_message, commit_message])


def process_dataset_chatbot(model_name, dataset, csv_writer):
    """Process the dataset and write results to the CSV file."""

    for item in dataset:
        diff = item['diff']
        original_message = item['message']
        message = [
            SystemMessage(content="Be a helpful assistant with knowledge of git message conventions."),
            HumanMessage(
                content=f"Summarize this git diff {diff}. into a useful, 10 words commit message. It is very important that you only provide the final output without any additional comments or remarks."),
        ]
        model_output = call_model_sync(model_name, message)
        csv_writer.writerow([original_message, model_output])


if __name__ == "__main__":
    print("Compiling LLMs")
    LLMS = {
        'deepinfra': ChatDeepInfra(model="databricks/dbrx-instruct", temperature=0),
        'codellama': ChatOllama(model="codellama", base_url="http://localhost:11434"),
        'mistral': LlamaMistralWrapper(),
        'phi_mini': PhiMiniWrapper()
    }
    # Create output directory
    print("Creating Output directory")
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load dataset
    print("Separating datasets")
    train_dataset, validation_dataset, test_dataset = import_dataset("Maxscha/commitbench")
    print(train_dataset.shape)

    print("Receiving model Names")
    model_name = input("Enter the model name: ")

    # Handle invalid input
    if model_name not in LLMS:
        print(f"Model {model_name} not found.")
        exit(1)

    # Prepare subset
    dataset_to_process = (
        train_dataset.select(random.sample(range(len(train_dataset)), 10))
    )

    # Write output to CSV
    output_file = os.path.join(output_dir, "output.csv")
    with open(output_file, mode="w", newline='', encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Original Message", "Model Output"])
        start_time = time.perf_counter()
        print(f"Start Time: {start_time}")
        if model_name == "mistral" or model_name == "phi_mini":
            process_dataset_quantized_instruct(model_name, dataset_to_process, csv_writer)
        else:
            process_dataset_chatbot(model_name, dataset_to_process, csv_writer)
        end_time = time.perf_counter()
        print(f"End Time: {end_time}")
        print(f"Total Time taken for executing train set is {end_time - start_time} ")
    # Display CSV content
    print(pd.read_csv(output_file))

    if 'phi_mini' in LLMS:
        LLMS['phi_mini'].close()
    del LLMS[model_name]
