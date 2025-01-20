# Commit Generation extension

>Notice: We used WSL2 and macOS as the testing environment, some adaptions for Windows are also implemented. However, they are not tested thoroughly. The current extension can be seen as a Proof of Concept.

To test if the extension is running properly, you need to follow the instructions below:

1. Open `extension/commit-generation` as the root project in Visual Studio Code.

2. Press `F5` to open the visual debugger, then press `Ctrl` + `Shift` + `P`, search and select `Generate commit message` in the list.

3. You should see the process by print statements in the console terminal, ignore the visual studio pop-ups - they are redundant for now.

4. After that you should see the console outputs(below is an example)：
```
Initializing virtual environments...
Virtual environment created. Now installing dependencies...
Pulling Mistral model via Ollama...
Dependencies installed. Now fetching git diff...
Git diff fetched:  Now write diff to temp file...
Diff file is written to temp file, located at /home/weicheng/.vscode-server/data/User/globalStorage/undefined_publisher.commit-generation/staged_diff.txt , now running the model to generate messages....
Message automatically copied to the file location: [.../my_messages.txt]
```
If you can see the last line, then messages should be copied to the file location, which is typically in the root folder of your repository.

### Model running on the extension
The extension runs on `src/runExtension.py`. The current model it is running:
```
Model: Mistral7b
Applied technique(s): few-shot
Temperature: 0.7
```

To adjust the parameters for the model, modify `src/runExtension.py`. Alternatively, you can put your own model in.

## Known Issues

In the case that `ollama serve` is run locally before starting the extension, the program will issue the following error:

>[ollama serve stderr]: Error: listen tcp 127.0.0.1:11434: bind: address already in use

To solve this, please kill the `ollama` process prior to starting the extension. See instructions on this [here](https://github.com/ollama/ollama/issues/690).

