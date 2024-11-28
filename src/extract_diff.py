from datasets import load_dataset

def import_dataset(dataset_name):
    dataset = load_dataset(dataset_name)

    # Load dataset in train, test, validation split
    train_dataset = dataset['train']
    validation_dataset = dataset['validation']
    test_dataset  = dataset['test']

    return train_dataset, validation_dataset, test_dataset


def process_diff(dataset):
    # TODO: check if diff needs to be processed
    pass
