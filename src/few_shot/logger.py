import os
import datetime

class Logger:
	def __init__(self, folder):
		current_folder = os.path.dirname(os.path.abspath(__file__))
		date_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

		self.log_file = current_folder + folder + f'/similar_logs_{date_time}.txt'

		if not os.path.exists(os.path.dirname(self.log_file)):
			os.makedirs(os.path.dirname(self.log_file))

	def print(self, message="", to_console=True):
		with open(self.log_file, 'a', encoding="utf-8") as f:
			f.write(message + '\n')
		
		if to_console:
			print(message)

	def flush(self):
		pass