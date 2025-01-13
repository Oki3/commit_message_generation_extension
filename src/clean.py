import os
import pandas as pd
import logging

def clean_string(message: str):
	return message.replace('\n', '').strip(' `"\'-')

def delete_empty_lines(message: str):
	return "\n".join(line for line in message.split('\n') if line.strip() not in ["", "```", "```bash", "```git"])

def clean_message(message: str, prompt_type: str):
	message = delete_empty_lines(message)

	if prompt_type == "cot":
		last_mention = message.lower().rfind("commit message")
		index = last_mention + 13
		
		if last_mention == -1:
			last_mention = message.lower().rfind("answer")
			index = last_mention + 6
		
		if last_mention != -1:
			next_colon = message[index:].find(":")

			if next_colon != -1:
				index += next_colon + 1

			message = delete_empty_lines(message[index:])
	
	message.replace("git commit -m", "")
	
	message = message.split('\n')[0]
	
	return clean_string(message)

def clean_item(df: pd.DataFrame, index: int, model: str, prompt_type: str):
	item = df.iloc[index]
	message = item['generated_message']

	if not isinstance(message, str):
		df.at[index, 'generated_message'] = ""
		df.at[index, 'cleaned_generated_message'] = ""
		df.at[index, 'single_line_generated_message'] = ""
		return

	logging.info(f"({index}, {model}, {prompt_type}) {message}")

	clean = clean_message(message, prompt_type)
	
	logging.info(f"({index}, {model}, {prompt_type}) {clean}")
	df.at[index, 'cleaned_generated_message'] = clean

def clean_file(input_path: str, output_path: str):
	df = pd.read_csv(input_path)

	parts = os.path.basename(input_path).replace('.csv','').split('_')
	model = parts[0]
	size = parts[1]
	prompt_type = parts[2]

	for i in range(len(df)):
		clean_item(df, i, model, prompt_type)

	df.to_csv(output_path, index=False)

def clean_folder(input_folder: str='./output', output_folder: str='./cleaned_output'):
	logging.basicConfig(filename='clean_output.log', level=logging.INFO, format='%(asctime)s - %(message)s')
	os.makedirs(output_folder, exist_ok=True)

	for filename in os.listdir(input_folder):
		if not filename.endswith('.csv'):
			continue

		input_path = os.path.join(input_folder, filename)
		output_path = os.path.join(output_folder, filename)

		clean_file(input_path, output_path)