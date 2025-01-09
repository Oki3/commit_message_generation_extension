import os
from git import Repo

from commit_similar import SimilarCommitSearch
from git import RemoteProgress
import sys
from logger import Logger

class ManagedRepo:
	author_name: str
	repo_name: str
	url: str
	folder: str
	repo: Repo
	logger: Logger

	def __init__(self, author: str, repo: str, logger: Logger, data_path: str='./data/'):
		self.author_name = author
		self.repo_name = repo
		self.logger = logger
		self.url = f'https://github.com/{author}/{repo}.git'

		current_folder = os.path.dirname(os.path.abspath(__file__))

		self.folder = current_folder + f'/../../{data_path}/{author}/{repo}'
	
	def is_cloned(self):
		return os.path.exists(self.folder)
	
	def clone(self):
		class CloneProgress(RemoteProgress):
			messages = {
				1: 'begin',
				2: 'end',
				3: 'stage mask',
				4: 'counting objects',
				5: 'enumerating objects',
				8: 'compressing objects',
				16: 'writing objects',
				34: 'size',
				32: 'receiving objects',
				64: 'resolving deltas',
				66: 'finished',
				128: 'finding sources',
				256: 'checking out files',
			}

			last_op_code = 0
			started = False

			def update(self, op_code, cur_count, max_count=None, message=''):
				if max_count:
					percent = (cur_count / max_count) * 100
					
					if self.messages.keys().__contains__(op_code):
						if op_code != self.last_op_code and self.started:
							print()
						
						if op_code == 34:
							message = f"Status: size | speed is {message}"
						else:
							message = f'Status: {self.messages.get(op_code, None)} at {percent:.2f}%' + "              "
						sys.stdout.write('\r'+message)

						self.last_op_code = op_code
						self.started = True

		self.logger.print(f'Cloning repository {self.repo_name} from {self.url}')
		self.repo = Repo.clone_from(self.url, self.folder, progress=CloneProgress())
		print()

	def get_similarity_search(self, padding: int):
		return SimilarCommitSearch(self.folder, self.logger, padding)