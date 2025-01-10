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

def baseline_prompt(diff: str) -> str:
	return f"""You are a programmer to produce concise, descriptive commit messages for Git changes. 
Do not include references to issue numbers or pull requests.

Now here is the new Git diff for which you must generate a commit message:
{diff}

Format:
A short commit message (in one sentence) describing what changed and why.

Output:
"""

def fewshot_prompt(diff: str, messages: list[str]) -> str:
	numbered_messages = '\n'.join([f"{i+1}. {message}" for i, message in enumerate(messages)])
	return f"""You are a programmer to produce concise, descriptive commit messages for Git changes. 
Below are up to three examples of commit messages that previously touched upon the same code or files. 
Please note that the first example is more important and should influence your message the most. 
Use the style and context of these examples, prioritizing the first examples, to inspire a new commit message for the provided Git diff. 
Do not include references to issue numbers or pull requests.

Examples of relevant commit messages:
{numbered_messages}

Now here is the new Git diff for which you must generate a commit message:
{diff}

Format:
A short commit message (in one sentence) describing what changed and why, consistent with the style 
and context demonstrated by the above examples.

Output:
"""

def cot_prompt(diff: str) -> str:
	return f"""You are a programmer to produce concise, descriptive commit messages for Git changes.
Do not include references to issue numbers or pull requests.

Now here is the new Git diff for which you must generate a commit message:
{diff}

Let's think step by step. Number every step before giving the final answer as [[ANSWER]] or ANSWER: ANSWER.

Steps:
"""

class BaselineExperiment(Experiment):
	def inputs(self):
		df = read_csv(self.folder + '/commitbench_subset.csv')

		items = []

		for i in range(self.size):
			item = df.iloc[i]

			diff = item['diff'] + "\n"
			prompt = baseline_prompt(diff)

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

			diff = item['diff']

			if item['nr_similar_commits_no_initial'] == 0:
				prompt = baseline_prompt(diff)
			else:
				messages = item['most_similar_commits_messages'].split('||-||')
				prompt = fewshot_prompt(diff, messages)

			items.append(InputItem(item['hash'], item['project'], item['message'], prompt))
		
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
			prompt = cot_prompt(diff)

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