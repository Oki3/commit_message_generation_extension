import os
from pandas import read_csv, DataFrame

# Directory of the current file
__FOLDER = os.path.dirname(os.path.abspath(__file__))

# Class representing a single input item for an experiment
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

	# Convert the input item to a list format for DataFrame compatibility
	def value(self):
		return [self.hash, self.project, self.true_message, self.prompt]

# Base class for all experiments
class Experiment:
	size: int
	folder: str

	def __init__(self, size: int, folder: str):
		self.size = size
		self.folder = folder

	# Method to generate input items for the experiment (to be implemented by subclasses)
	def inputs(self) -> list[InputItem]:
		return []
	
	# Method to return the name of the experiment (to be implemented by subclasses)
	def name(self) -> str:
		return ""

# Generate a baseline prompt based on the given diff
def baseline_prompt(diff: str) -> str:
	return f"""You are a programmer to produce concise, descriptive commit messages for Git changes. 
Do not include references to issue numbers or pull requests.

Now here is the new Git diff for which you must generate a commit message:
{diff}

Format:
A short commit message (in one sentence) describing what changed and why.

Output:
"""

# Generate a few-shot prompt based on the given diff and example messages
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

# Generate a chain-of-thought (CoT) prompt based on the given diff
def cot_prompt(diff: str) -> str:
	return f"""You are a programmer to produce concise, descriptive commit messages for Git changes.
Do not include references to issue numbers or pull requests.

Now here is the new Git diff for which you must generate a commit message:
{diff}

Let's think step by step. Number every step before giving the final answer as [[ANSWER]] or ANSWER: ANSWER.

Steps:
"""

# Baseline experiment that uses the baseline prompt
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

# Few-shot experiment that uses the few-shot prompt
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

# Chain-of-Thought (CoT) experiment that uses the CoT prompt
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

# List of supported models
MODELS = ["mistral", "codellama", "phi3.5"]

# Size of the input data for experiments
SIZE = 1000

# List of experiments to run
EXPERIMENTS = [BaselineExperiment(SIZE, __FOLDER), FewShotExperiment(SIZE, __FOLDER), CoTExperiment(SIZE, __FOLDER)]

# Folder for input data
FOLDER = __FOLDER + '/../input'

# Ensure the input folder exists
os.makedirs(FOLDER, exist_ok=True)

# Generate input CSV files for each model and experiment
for model in MODELS:
	for experiment in EXPERIMENTS:
		items = experiment.inputs()

		# Create a DataFrame to store the experiment inputs
		df = DataFrame(columns=["hash", "project", "true_message", "prompt"])

		for item in items:
			df.loc[len(df)] = item.value()

		# Save the DataFrame as a CSV file
		df.to_csv(f"{FOLDER}/{model}_{SIZE}_{experiment.name()}.csv", index=False)