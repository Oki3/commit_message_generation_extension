# Team 3
Group project (Team 3) for CS4570 Machine Learning for Software Engineering. This repository serves as a basis for research into prompt engineering for automated commit message generation. 

## Requirements

- Python 3.10 or higher
- [Ollama](https://github.com/jmorganca/ollama) (for model serving)
- A supported Ollama model (e.g. `mistral`, `codellama`, `phi3.5`)

## Installation

### 1. Install Python and Dependencies

1. **Python**  
   Make sure you have Python 3.10 or higher installed. If you are on a Unix-like system (Linux/MacOS), run:
   ```bash
   python3 --version
   ```
   If Python is not installed, visit [python.org](https://www.python.org/downloads/) to download and install it.

2. **Python Dependencies**  
   Install the required Python libraries using pip:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Install Ollama

Ollama is required to run and manage the models. Download and install Ollama from [ollama.com](https://ollama.com/).

### 3. Install a Model

Ollama requires a model to be installed before you can generate text. Some possible models include:
- `mistral`
- `codellama`
- `phi3.5`

To install a model (for example, `mistral`), run:
```bash
ollama pull mistral
```

## Usage

Before usage make sure Ollama is running using:
```bash
ollama serve
```

Below is an example of how to run the main file:
```bash
python src/main.py \
    --model mistral \
    --prompt baseline \
```

## Man page

Below is the placeholder for the detailed manual page of the main file and how to use it:

```
sage: main.py [-h] [--model {mistral,codellama,phi3.5}] [--prompt {baseline,fewshot,cot}] [--input_size INPUT_SIZE] [--process_amount PROCESS_AMOUNT] [--sequential] [--input_folder INPUT_FOLDER] [--output_folder OUTPUT_FOLDER] [--temperature TEMPERATURE] [--workers WORKERS]

Run one of the experiments with the specified model.

options:
  -h, --help            show this help message and exit
  --model {mistral,codellama,phi3.5}
                        The model to use.
  --prompt {baseline,fewshot,cot}
                        The prompt to use.
  --input_size INPUT_SIZE
                        The size of the input.
  --process_amount PROCESS_AMOUNT
                        The number of items to process.
  --sequential          Run the experiment sequentially instead of in parallel.
  --input_folder INPUT_FOLDER
                        The folder containing the input files.
  --output_folder OUTPUT_FOLDER
                        The folder to save the output files.
  --temperature TEMPERATURE
                        The temperature for the model generation.
  --workers WORKERS     The number of workers to use for parallel processing.
```

## Other scripts
### Input preperation
Run `prepare_input.py` to transform the dataset `csv` files into input files, by generating the prompts from them. The input files are generated as `{model}_{size}_{technique}.csv`.
```bash
python src/prepare_input.py
```

### Run similar search
Run `run_similar_search.py` to find similar commits as few shot examples for samples in the dataset. Warning: this script will download full repositories to find similar commits and so will usage a large amount of storage.
```bash
python src/few_shot/run_similar_search.py
```