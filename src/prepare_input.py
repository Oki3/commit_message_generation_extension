import os
from pandas import read_csv, DataFrame

__FOLDER = os.path.dirname(os.path.abspath(__file__))

class InputItem:
	hash: str
	project: str
	true_message: str
	prompt: str

	def __init__(self, hash: str, project: str, true_message: str, prompt: str):
		self.hash = hash
		self.project = project
		self.true_message = true_message
		self.prompt = prompt

	def value(self):
		return [self.hash, self.project, self.true_message, self.prompt]

class Experiment:
	size: int
	folder: str

	def __init__(self, size: int, folder: str):
		self.size = size
		self.folder = folder

	def inputs(self) -> list[InputItem]:
		return []
	
	def name(self) -> str:
		return ""

class BaselineExperiment(Experiment):
	def inputs(self):
		df = read_csv(self.folder + '/commitbench_subset.csv')

		items = []

		for i in range(self.size):
			item = df.iloc[i]

			diff = item['diff'] + "\n"
			prompt = f"{diff}You are a programmer who makes the above code changes. Please write a commit message for the above code changes."

			items.append(InputItem(item['hash'], item['project'], item['message'], prompt))
		
		return items
	
	def name(self):
		return "baseline"

class FewShotExperiment(Experiment):
	def inputs(self):
		df = read_csv(self.folder + '/commitbench_subset_similar.csv')

		items = []

		for i in range(self.size):
			item = df.iloc[i]

			items.append(InputItem(item['hash'], item['project'], item['message'], item['prompt']))
		
		return items
	
	def name(self):
		return "fewshot"
	
class CoTExperiment(Experiment):
	def inputs(self):
		df = read_csv(self.folder + '/commitbench_subset_similar.csv')

		items = []

		for i in range(self.size):
			item = df.iloc[i]

			diff = item['diff'] + "\n"
			prompt = f"""{diff}You are a programmer who makes the above code changes. Please write a commit message for the above code changes.
Let's think step by step. Inside the answer, write the git commit message in the following format:
### COMMIT MESSAGE ###
[The generated commit message]
### END COMMIT MESSAGE ###"""

			items.append(InputItem(item['hash'], item['project'], item['message'], prompt))
		
		return items
	
	def name(self):
		return "cot"

MODELS = ["mistral", "codellama", "phi3.5"]
SIZE = 1000
EXPERIMENTS = [BaselineExperiment(SIZE, __FOLDER), FewShotExperiment(SIZE, __FOLDER), CoTExperiment(SIZE, __FOLDER)]
FOLDER = __FOLDER + '/../input'

os.makedirs(FOLDER, exist_ok=True)

for model in MODELS:
	for experiment in EXPERIMENTS:
		items = experiment.inputs()

		df = DataFrame(columns=["hash", "project", "true_message", "prompt"])

		for item in items:
			df.loc[len(df)] = item.value()

		df.to_csv(f"{FOLDER}/{model}_{SIZE}_{experiment.name()}.csv", index=False)