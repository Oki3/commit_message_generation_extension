import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    let generatedMessage = '';

    try {
        const repoPath = path.resolve(__dirname, '../../../');

        // virtual environment initialization
        const venvPath = path.join(repoPath, '.venv');
        const isWindows = process.platform === 'win32';
        const venvPython = isWindows
            ? path.join(venvPath, 'Scripts', 'python.exe')
            : path.join(venvPath, 'bin', 'python');
        const venvPip = isWindows
            ? path.join(venvPath, 'Scripts', 'pip.exe')
            : path.join(venvPath, 'bin', 'pip');
        
        // create the virtual environment if it doesn't exist
        const createVenvIfNeeded = async (): Promise<void> => {
            return new Promise((resolve, reject) => {
                if (fs.existsSync(venvPath)) {
                    // If .venv already exists, just resolve immediately
                    resolve();
                } else {
                    vscode.window.showInformationMessage('Creating virtual environment...');
                    
                    // Adjust 'python' to 'python3' or other as needed on your system
                    const pythonCmd = isWindows ? 'python' : 'python3';
                    const createVenv = spawn(
                        pythonCmd,
                        ['-m', 'venv', venvPath],
                        { cwd: repoPath }
                    );

                    createVenv.stderr.on('data', (data) => {
                        vscode.window.showErrorMessage(`Error creating .venv: ${data}`);
                    });

                    createVenv.on('close', (code) => {
                        if (code !== 0) {
                            reject(new Error(`Failed to create .venv. Exit code: ${code}`));
                        } else {
                            resolve();
                        }
                    });
                }
            });
        };

        // install requirements if they exist
        const installRequirements = async (): Promise<void> => {
            return new Promise((resolve, reject) => {
                const requirementsPath = path.join(repoPath, 'requirements.txt');
                if (!fs.existsSync(requirementsPath)) {
                    vscode.window.showWarningMessage('No requirements.txt found. Skipping install.');
                    resolve();
                    return;
                }
                
                vscode.window.showInformationMessage('Installing requirements in .venv...');

                // Instead of `source .venv/bin/activate && pip install ...`,
                // call the venv's pip directly:
                const installCmd = spawn(
                    venvPip, 
                    ['install', '-r', requirementsPath], 
                    { cwd: repoPath }
                );

                installCmd.stderr.on('data', (data) => {
                    vscode.window.showErrorMessage(`Pip error: ${data}`);
                });

                installCmd.on('close', (code) => {
                    if (code !== 0) {
                        reject(new Error(`pip install failed. Exit code: ${code}`));
                    } else {
                        resolve();
                    }
                });
            });
        };

        // Create a helper function to pull the Mistral model via Ollama
        async function pullModel(repoPath: string): Promise<void> {
            return new Promise((resolve, reject) => {
                // spawn 'ollama pull mistral' in the specified repo directory
                const pullProcess = spawn('ollama', ['pull', 'mistral'], { cwd: repoPath });

                // Capture any output if needed
                pullProcess.stdout.on('data', (data) => {
                    console.log(`[ollama pull mistral] stdout: ${data}`);
                });
                pullProcess.stderr.on('data', (data) => {
                    console.error(`[ollama pull mistral] stderr: ${data}`);
                });

                pullProcess.on('close', (code) => {
                    if (code !== 0) {
                        reject(new Error(`ollama pull mistral failed. Exit code: ${code}`));
                    } else {
                        resolve();
                    }
                });
            });
        }


        // git diff
        const getGitDiff = async (): Promise<string> => {
            return new Promise((resolve, reject) => {
                const gitDiffProcess = spawn('git', ['diff'], { cwd: repoPath });
                let gitDiff = '';

                gitDiffProcess.stdout.on('data', (data) => {
                    gitDiff += data.toString();
                });

                gitDiffProcess.stderr.on('data', (data) => {
                    vscode.window.showErrorMessage(`Error: ${data.toString()}`);
                });

                gitDiffProcess.on('close', (code) => {
                    if (code === 0) {
                        resolve(gitDiff);
                    } else {
                        reject(new Error(`git diff exited with code ${code}`));
                    }
                });
            });
        };

        // Run the Python script from .venv
        const runPythonScript = async (scriptArgs: string[]) => {
            return new Promise<void>((resolve, reject) => {
                // If your script is at `src/main.py`, we can call it directly with the venv Python
                const pythonProcess = spawn(
                    venvPython,
                    scriptArgs,
                    { cwd: repoPath }
                );

                // Gather stdout (for commit message, etc.)
                pythonProcess.stdout.on('data', (data) => {
                    vscode.window.showInformationMessage(`Output: ${data}`);
                    generatedMessage += data.toString();
                });

                pythonProcess.on('close', (code) => {
                    if (code !== 0) {
                        reject(new Error(`Python script exited with code ${code}`));
                    } else {
                        resolve();
                        vscode.env.clipboard.writeText(generatedMessage.trim());
                    }
                });
            });
        };

        // Wrap all in an async IIFE to manage flow
        (async () => {
            console.log("Initializing virtual environments...");
            await createVenvIfNeeded();

            console.log("Virtual environment created. Now installing dependencies...");
            await installRequirements();

            // pull the Mistral model via Ollama
            console.log("Pulling Mistral model via Ollama...");
            await pullModel(repoPath);

            console.log("Dependencies installed. Now fetching git diff...");
            const gitDiff = await getGitDiff();
            if (!gitDiff.trim()) {
                vscode.window.showWarningMessage('No staged changes found.');
                return;
            }

            console.log("Git diff fetched: ",
                       // gitDiff, 
                        "Now write diff to temp file...");
            const tempDir = context.globalStorageUri.fsPath;
            if (!fs.existsSync(tempDir)) {
                fs.mkdirSync(tempDir, { recursive: true });
            }
            const tempFilePath = path.join(tempDir, 'staged_diff.txt');
            fs.writeFileSync(tempFilePath, gitDiff);

            console.log("Diff file is written to temp file, located at", tempFilePath, ", now running the model to generate messages....")
            

            //     Run the Python script inside the venv
            //     (assuming the script is `src/main.py --model mistral --prompt baseline`)
            //     You might need to pass the path to your tempFilePath as well if your Python script uses it.
            const outputTxtPath = path.join(repoPath, 'my_messages.txt');
            await runPythonScript(['src/runExtension.py', '--txt_file', tempFilePath, '--output_txt', outputTxtPath]);
            console.log("Message automatically copied to the file location: ", outputTxtPath);

        })().catch((error) => {
            vscode.window.showErrorMessage(`Extension activation error: ${error.message}`);
        });

    } catch (error: unknown) {
        if (error instanceof Error) {
            vscode.window.showErrorMessage(`Failed to initialize: ${error.message}`);
        } else {
            vscode.window.showErrorMessage('Failed to initialize: Unknown error occurred.');
        }
    }

    const disposable = vscode.commands.registerCommand('commit-generation.generateMessage', () => {
        // Copy the generated message to clipboard
        vscode.env.clipboard.writeText(generatedMessage.trim());
        vscode.window.showInformationMessage('Commit message generated and copied to clipboard!');
    });

    context.subscriptions.push(disposable);
}

// Deactivate
export function deactivate() {}
