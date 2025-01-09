import os
from pandas import read_csv, DataFrame
import requests

current_folder = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = current_folder + '/../commitbench_subset_similar.csv'
OUTPUT_FILE = current_folder + '/../commitbench_subset_similar_output.csv'
ITEMS = 10

df = read_csv(DATA_FILE)

output_df = DataFrame(columns=["hash", "project", "correct", "mistral"])

for i in range(ITEMS):
	item = df.iloc[i]
	prompt = item['prompt']
	url = "http://localhost:11434/api/generate"
	data = {
		"model": "mistral",
		"prompt": prompt,
		"stream": False
	}
	response = requests.post(url, json=data)
	mistral_output = response.json()

	print(f"({i+1}/{ITEMS}) {item['project']} - {item['hash']} - {mistral_output['response']}")

	output_df.loc[i] = [
		item['hash'],
		item['project'],
		item['message'],
		mistral_output['response'].strip()
	]

output_df.to_csv(OUTPUT_FILE, index=False)