from datasets import load_dataset


def import_dataset(dataset_name):
    dataset = load_dataset(dataset_name)

    # Load dataset in train, test, validation split
    train_dataset = dataset['train']
    validation_dataset = dataset['validation']
    test_dataset  = dataset['test']

    return train_dataset, validation_dataset, test_dataset

def import_subset_for_local_machine(dataset_name):
    dataset = load_dataset(dataset_name)
    train_df=dataset['train'].to_pandas()
    subset= train_df.sample(n=1000,random_state=42)
    subset.to_csv("commitbench_subset.csv",index=False)
    print("Subset saved as commitbench_subset.csv")

def process_diff(dataset):
    # TODO: check if diff needs to be processed
    pass

