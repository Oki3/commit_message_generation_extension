import os
import pandas as pd

# Method to extract the generated messages
def extract_generated_messages(file_path, output_file):
    # Load the CSV file
    data = pd.read_csv(file_path)

    # Check if the required column exists
    if 'generated_message' not in data.columns:
        raise ValueError("The column 'generated_message' does not exist in the file.")

    # Extract the 'generated_message' column
    generated_messages = data['generated_message']

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save to a new file
    generated_messages.to_csv(output_file, index=False, header=True)
    print(f"Generated messages have been saved to {output_file}")

# Process all CSV files in the input directory
def process_all_files(input_directory, output_directory):
    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Iterate through all files in the input directory
    for file_name in os.listdir(input_directory):
        if file_name.endswith('.csv'):
            input_file = os.path.join(input_directory, file_name)
            output_file = os.path.join(output_directory, f"{os.path.splitext(file_name)[0]}_generated_commit_messages.csv")
            extract_generated_messages(input_file, output_file)

# Input and output directories
input_directory = './output'  
output_directory = './commit_messages'  

# Run the extraction for all files
if __name__ == "__main__":
    process_all_files(input_directory, output_directory)