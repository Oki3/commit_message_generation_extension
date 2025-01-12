import os
import datetime

# A simple logging utility to write log messages to a file and optionally display them on the console
class Logger:
	def __init__(self, name: str, folder: str = "./logs"):
		# Generate a timestamp for unique log file naming
		date_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

		# Construct the log file path
		self.log_file = folder + f'/{name}_{date_time}.txt'

		# Create the directory if it does not exist
		if not os.path.exists(os.path.dirname(self.log_file)):
			os.makedirs(os.path.dirname(self.log_file))

	# Write a log message to the log file and optionally print it to the console
	def print(self, message="", to_console=True):
		with open(self.log_file, 'a', encoding="utf-8") as f:
			f.write(message + '\n')
		
		if to_console:
			print(message)

	# Placeholder method for compatibility with logging interfaces requiring a flush method but currently does nothing.
	def flush(self):
		pass