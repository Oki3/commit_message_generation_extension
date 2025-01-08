from math import ceil
from commit_similar import SimilarCommitSearch
import os
from pandas import DataFrame, read_csv

from repo import ManagedRepo

class SimilaritySearchExperiment:
	df: DataFrame

	def __init__(self, input_file: str, output_file: str, items: int = 10):
		self.input_file = input_file
		self.output_file = output_file
		self.items = items

	def empty_prompt(self, diff: str):
		return f"""Instruction:
You are an AI assistant designed to produce concise, descriptive commit messages for Git changes. 
You will be given a Git diff that shows the modifications made to the code. 
Your task is to create a clear, single-sentence commit message that accurately describes 
what was changed and why.

Now here is the new Git diff for which you must generate a commit message:
{diff}

Output:
A short commit message (in one sentence) describing what changed and why.
"""

	def few_shot_prompt(self, diff: str, messages: list[str]):
		numbered_messages = '\n'.join([f"{i+1}. {message}" for i, message in enumerate(messages)])
		return f"""Instruction:
You are an AI assistant designed to produce concise, descriptive commit messages for Git changes. 
Below are up to three examples of commit messages that previously touched upon the same code or files. 
Please note that the first example is more important and should influence your message the most. 
Use the style and context of these examples, prioritizing the first examples, to inspire a new commit message for the provided Git diff.

Examples of relevant commit messages:
{numbered_messages}

Now here is the new Git diff for which you must generate a commit message:
{diff}

Output:
A short commit message (in one sentence) describing what changed and why, consistent with the style 
and context demonstrated by the above examples.
"""
	
	def read(self):
		return read_csv(self.input_file)
	
	def save(self):
		self.df.to_csv(self.output_file, index=False)

	def handle_item(self, item: dict, i: int):
		prompt = ""

		try:
			project_text = item['project']
			author, project = project_text.split('_', 1)
			
			print(f"({i}) Handeling commit {item['hash'][:7]} found at https://github.com/{author}/{project}/commit/{item['hash'][:7]}")

			repo = ManagedRepo(author, project)

			if not repo.is_cloned():
				repo.clone()
			else:
				print("Repo already cloned")

			hash = item['hash']
			diff_from = f"{hash}~"
			diff_to = hash

			sim = repo.get_similarity_search()
			commit_scores = sim.search(diff_from=diff_from, diff_to=diff_to, only_staged=False)

			print(f"Found {len(commit_scores)} commits (sorteed by score):")

			for commit_score in commit_scores:
				print(f"|> {commit_score.commit.hash[:7]} - w {commit_score.score:.4f} ({commit_score.commit.message[:128]})")

			# Remove commit if the commit hash is the same as the current commit
			commit_scores = [commit_score for commit_score in commit_scores if commit_score.commit.hash != hash]

			self.df.at[item.name, 'nr_similar_commits'] = len(commit_scores)

			# Only keep the three heighest score commits at most
			commit_scores = commit_scores[:3]

			self.df.at[item.name, 'nr_similar_commits_capped'] = len(commit_scores)

			# Remove overlap if the commit message is "Initial commit"
			commit_scores = [commit_score for commit_score in commit_scores if commit_score.commit.message != "Initial commit"]

			self.df.at[item.name, 'nr_similar_commits_no_initial'] = len(commit_scores)

			if len(commit_scores) > 0:
				print(f"Selected {len(commit_scores)} commits:")
				for commit_score in commit_scores:
					print(f"|> https://github.com/{author}/{project}/commit/{commit_score.commit.hash[:7]}")
			else:
				print("No commits found")

			commits = [commit_score.commit for commit_score in commit_scores]

			self.df.at[item.name, 'most_similar_commits'] = ', '.join([commit.hash for commit in commits])

			messages = [commit.message for commit in commits]

			if len(messages) > 0:
				prompt = self.few_shot_prompt(item['diff'], messages)
			else:
				prompt = self.empty_prompt(item['diff'])
		except Exception as e:
			print(f"Error: {e}")
			self.df.at[item.name, 'nr_similar_commits'] = 0
			self.df.at[item.name, 'nr_similar_commits_capped'] = 0
			self.df.at[item.name, 'nr_similar_commits_no_initial'] = 0
			self.df.at[item.name, 'most_similar_commits'] = ''
			prompt = self.empty_prompt(item['diff'])

		print(f"Prompt is {len(prompt)} characters or ~{self.estimate_prompt_tokens(prompt)} tokens")

		self.df.at[item.name, 'prompt'] = prompt

	def estimate_prompt_tokens(self, prompt: str):
		return ceil(len(prompt.replace("\n", " ").split(" ")) * 1.6)

	def run(self):
		self.df = self.read()

		for i in range(self.items):
			self.handle_item(self.df.iloc[i], i)

			print()

		self.save()

current_folder = os.path.dirname(os.path.abspath(__file__))

ITEMS = 1
INPUT_FILE = current_folder + '/../commitbench_subset.csv'
OUTPUT_FILE = current_folder + '/../commitbench_subset_similar.csv'

experiment = SimilaritySearchExperiment(INPUT_FILE, OUTPUT_FILE, ITEMS)
experiment.run()
