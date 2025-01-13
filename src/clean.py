import os
import pandas as pd

def clean_output_files(input_folder='./output', output_folder='./cleaned_output'):
	os.makedirs(output_folder, exist_ok=True)

	for filename in os.listdir(input_folder):
		if not filename.endswith('.csv'):
			continue

		df = pd.read_csv(os.path.join(input_folder, filename))
		parts=filename.replace('.csv','').split('_')
		model=parts[0]
		prompt_type=parts[2]

		for i in range(len(df)):
			item = df.iloc[i]
			message = item['generated_message']

			print(f"({i}) {message}")

			if not isinstance(message, str):
				df.at[i, 'generated_message'] = ""
				continue

			message1 = message
			message1 = "\n".join([line for line in message1.split('\n') if line.strip() != ""])

			if prompt_type == "cot":
				if 'answer' in message1.lower():
					end = message1.lower().rfind('answer')

					message1 = message1[end+7:]
				elif '[[' in message:
					message1 = message1.split('[[')[1].split(']]')[0]
			
			message1 = message1.strip('"`').strip("'")
			print(f"({i}) {message1}")
			df.at[i, 'cleaned_generated_message'] = message1

			message2 = message1

			if prompt_type == "cot":
				message2 = message2.split('\n')[-1]
			else:
				if " here is" in message2.split('\n')[0].lower() and len(message2.split('\n')) > 1:
					message2 = message2.split('\n')[1]
				else:
					message2 = message2.split('\n')[0]

			message2 = message2.strip('"`').strip("'")

			print(f"({i}) {message2}")
			df.at[i, 'aggressive_cleaned_generated_message'] = message2

		df.to_csv(os.path.join(output_folder, filename), index=False)