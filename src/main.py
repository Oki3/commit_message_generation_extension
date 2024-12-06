import csv
import os
import random

import pandas as pd
from dotenv import load_dotenv
from langchain_community.chat_models import ChatDeepInfra
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from CodeT5Wrapper import CodeT5Wrapper
from extract_diff import import_dataset

load_dotenv()

LLMS = {
    'deepinfra': ChatDeepInfra(model="databricks/dbrx-instruct", temperature=0),
    'codellama': ChatOllama(model="codellama", base_url="http://localhost:11434"),
    'codet5': CodeT5Wrapper(model_name="Salesforce/codet5-base")
}


def call_model_sync(model, messages):
    """Call given model with given prompts."""
    llm = LLMS[model]
    return llm.invoke(messages) if model == "codet5" else llm.invoke(messages).content


def process_dataset(model_name, dataset, csv_writer):
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
    # Create output directory
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load dataset
    train_dataset, validation_dataset, test_dataset = import_dataset("Maxscha/commitbench")

    model_name = input("Enter the model name: ")

    # Handle invalid input
    if model_name not in LLMS:
        print(f"Model {model_name} not found.")
        exit(1)

    # Prepare subset for specific models
    dataset_to_process = (
        train_dataset.select(random.sample(range(len(train_dataset)), 10))
        if model_name == "codet5" else train_dataset
    )

    # Write output to CSV
    output_file = os.path.join(output_dir, "output.csv")
    with open(output_file, mode="w", newline='', encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Original Message", "Model Output"])
        process_dataset(model_name, dataset_to_process, csv_writer)

    # Display CSV content
    print(pd.read_csv(output_file))
