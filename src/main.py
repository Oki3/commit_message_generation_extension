import os

from dotenv import load_dotenv
from langchain_community.chat_models import ChatDeepInfra
from langchain_core.messages import HumanMessage, SystemMessage

from extract_diff import import_dataset

load_dotenv()


def call_model_sync(messages):
    llm = ChatDeepInfra(model="databricks/dbrx-instruct", temperature=0)
    resp = llm(messages)
    resp.messages = messages
    resp.user = username
    return resp


if __name__ == "__main__":
    # Access the environment variables
    username = os.getenv("USERNAME")

    # TODO: check whether we agree with this dataset
    train_dataset, validation_dataset, test_dataset = import_dataset("Maxscha/commitbench")

    # Test with singular diff from train dataset
    message = [
        SystemMessage(
            content="Be a helpful assistant with knowledge of git message conventions."
        ),
        HumanMessage(
            content="Summarize this git diff into a useful, 10 words commit message: " + train_dataset[0]['diff']
        )
    ]

    res = call_model_sync(message)
    print(res)
