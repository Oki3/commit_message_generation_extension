"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
let ollamaProcess = null;
function activate(context) {
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
        const createVenvIfNeeded = async () => {
            return new Promise((resolve, reject) => {
                if (fs.existsSync(venvPath)) {
                    // If .venv already exists, just resolve immediately
                    resolve();
                }
                else {
                    vscode.window.showInformationMessage('Creating virtual environment...');
                    // Adjust 'python' to 'python3' or other as needed on your system
                    const pythonCmd = isWindows ? 'python' : 'python3';
                    const createVenv = (0, child_process_1.spawn)(pythonCmd, ['-m', 'venv', venvPath], { cwd: repoPath });
                    createVenv.stderr.on('data', (data) => {
                        vscode.window.showErrorMessage(`Error creating .venv: ${data}`);
                    });
                    createVenv.on('close', (code) => {
                        if (code !== 0) {
                            reject(new Error(`Failed to create .venv. Exit code: ${code}`));
                        }
                        else {
                            resolve();
                        }
                    });
                }
            });
        };
        // install requirements if they exist
        const installRequirements = async () => {
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
                const installCmd = (0, child_process_1.spawn)(venvPip, ['install', '-r', requirementsPath], { cwd: repoPath, stdio: 'inherit' });
                // installCmd.stderr.on('data', (data) => {
                //     vscode.window.showErrorMessage(`Pip error: ${data}`);
                // });
                installCmd.on('close', (code) => {
                    if (code !== 0) {
                        reject(new Error(`pip install failed. Exit code: ${code}`));
                    }
                    else {
                        resolve();
                    }
                });
            });
        };
        async function startOllamaServer(repoPath) {
            return new Promise((resolve, reject) => {
                // 1) Spawn 'ollama serve'
                ollamaProcess = (0, child_process_1.spawn)('ollama', ['serve'], { cwd: repoPath });
                // 2) Listen to stdout
                ollamaProcess.stdout.on('data', (data) => {
                    const line = data.toString();
                    console.log(`[ollama serve stdout]: ${line}`);
                    // Once we see a "Listening on ..." line, we can assume the server is up.
                    if (line.toLowerCase().includes('listening on')) {
                        resolve();
                    }
                });
                ollamaProcess.stderr.on('data', (data) => {
                    console.error(`[ollama serve stderr]: ${data}`);
                });
                // If the process closes unexpectedly before we see "Listening on..."
                ollamaProcess.on('close', (code) => {
                    if (code !== 0) {
                        reject(new Error(`ollama serve exited with code ${code}`));
                    }
                });
                setTimeout(() => {
                    // If the process hasn’t exited, assume it's running
                    resolve();
                }, 5000);
            });
        }
        // Create a helper function to pull the Mistral model via Ollama
        async function pullModel(repoPath) {
            return new Promise((resolve, reject) => {
                // spawn 'ollama pull mistral' in the specified repo directory
                const pullProcess = (0, child_process_1.spawn)('ollama', ['pull', 'mistral'], { cwd: repoPath });
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
                    }
                    else {
                        resolve();
                    }
                });
            });
        }
        // // git diff
        // const getGitDiff = async (): Promise<string> => {
        //     return new Promise((resolve, reject) => {
        //         const gitDiffProcess = spawn('git', ['diff','--cached'], { cwd: repoPath });
        //         let gitDiff = '';
        //         gitDiffProcess.stdout.on('data', (data) => {
        //             gitDiff += data.toString();
        //         });
        //         gitDiffProcess.stderr.on('data', (data) => {
        //             vscode.window.showErrorMessage(`Error: ${data.toString()}`);
        //         });
        //         gitDiffProcess.on('close', (code) => {
        //             if (code === 0) {
        //                 resolve(gitDiff);
        //             } else {
        //                 reject(new Error(`git diff exited with code ${code}`));
        //             }
        //         });
        //     });
        // };
        // 1) We remove getGitDiff usage entirely.
        // 2) We'll define a new method that spawns git diff, collects the diff, then spawns python:
        async function runPythonScriptWithPipedDiff() {
            return new Promise((resolve, reject) => {
                generatedMessage = '';
                let diffCollected = "";
                // A) Spawn 'git diff --cached'
                const gitProcess = (0, child_process_1.spawn)('git', ['diff', '--cached'], { cwd: repoPath });
                // B) Accumulate its stdout into diffCollected
                gitProcess.stdout.on('data', (chunk) => {
                    diffCollected += chunk.toString();
                });
                // Optionally capture errors
                gitProcess.stderr.on('data', (errData) => {
                    vscode.window.showErrorMessage(`git diff error: ${errData}`);
                });
                // C) When git diff finishes
                gitProcess.on('close', (gitCode) => {
                    if (gitCode !== 0) {
                        reject(new Error(`git diff --cached exited with code ${gitCode}`));
                        return;
                    }
                    // Check if the diff is empty
                    if (!diffCollected.trim()) {
                        vscode.window.showWarningMessage('No staged changes found.');
                        resolve();
                        return;
                    }
                    diffCollected += `
            Format:
            A short commit message (in one sentence) describing what changed and why, consistent with the style 
            and context demonstrated by the above examples.

            Output:`;
                    // D) Now spawn Python
                    const pyProcess = (0, child_process_1.spawn)(venvPython, 
                    // for example: ['src/runExtension.py', '--output_txt', 'my_messages.txt']
                    // or any other arguments your script needs:
                    ['src/runExtension.py', '--output_txt', 'my_messages.txt'], { cwd: repoPath });
                    // E) When Python writes to stdout, accumulate the generated message
                    pyProcess.stdout.on('data', (data) => {
                        //vscode.window.showInformationMessage(`Output: ${data}`);
                        generatedMessage += data.toString();
                    });
                    // (Optional) handle Python stderr
                    pyProcess.stderr.on('data', (data) => {
                        console.error(`[Python stderr]: ${data}`);
                    });
                    // F) On Python close
                    pyProcess.on('close', async (pyCode) => {
                        if (pyCode !== 0) {
                            reject(new Error(`Python script exited with code ${pyCode}`));
                        }
                        else {
                            console.log('Full generated message:', generatedMessage.trim());
                            console.log('About to show QuickPick with options:', generatedMessage.trim());
                            const options = [
                                { label: '✅ Accept', detail: generatedMessage.trim() },
                                { label: '❌ Reject', detail: 'Do not use this commit message.' },
                            ];
                            const selection = await vscode.window.showQuickPick(options, {
                                placeHolder: 'Review the generated commit message and choose an action.',
                            });
                            if (selection?.label === '✅ Accept') {
                                vscode.env.clipboard.writeText(generatedMessage.trim());
                                vscode.window.showInformationMessage('Commit message accepted and copied to clipboard!');
                            }
                            else if (selection?.label === '❌ Reject') {
                                vscode.window.showWarningMessage('Commit message rejected.');
                            }
                            else {
                                vscode.window.showWarningMessage('No action taken.');
                            }
                            resolve();
                        }
                    });
                    // G) Finally, write the collected diff to Python’s stdin
                    pyProcess.stdin.write(diffCollected);
                    pyProcess.stdin.end();
                });
            });
        }
        // Run the Python script from .venv
        const runPythonScript = async (scriptArgs) => {
            return new Promise((resolve, reject) => {
                const pythonProcess = (0, child_process_1.spawn)(venvPython, scriptArgs, { cwd: repoPath });
                // Gather stdout (for commit message, etc.)
                pythonProcess.stdout.on('data', (data) => {
                    vscode.window.showInformationMessage(`Output: ${data}`);
                    generatedMessage += data.toString();
                });
                pythonProcess.on('close', async (code) => {
                    if (code !== 0) {
                        reject(new Error(`Python script exited with code ${code}`));
                    }
                    else {
                        console.log(generatedMessage.trim());
                        resolve();
                        vscode.env.clipboard.writeText(generatedMessage.trim());
                        vscode.window.showInformationMessage('Commit message has been generated and copied to clipboard!');
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
            console.log("Starting Ollama server...");
            await startOllamaServer(repoPath);
            // pull the Mistral model via Ollama
            console.log("Pulling Mistral model via Ollama...");
            await pullModel(repoPath);
            console.log("Dependencies installed. Now fetching git diff...");
            console.log("Piping staged diff to Python...");
            await runPythonScriptWithPipedDiff();
        })().catch((error) => {
            vscode.window.showErrorMessage(`Extension activation error: ${error.message}`);
        });
    }
    catch (error) {
        if (error instanceof Error) {
            vscode.window.showErrorMessage(`Failed to initialize: ${error.message}`);
        }
        else {
            vscode.window.showErrorMessage('Failed to initialize: Unknown error occurred.');
        }
    }
    const disposable = vscode.commands.registerCommand('commit-generation.generateMessage', () => {
        // Copy the generated message to clipboard
        vscode.env.clipboard.writeText(generatedMessage.trim());
        vscode.window.showInformationMessage('Commit message generation is ongoing.');
    });
    context.subscriptions.push(disposable);
}
// Deactivate
function deactivate() {
    if (ollamaProcess) {
        console.log('Stopping Ollama server...');
        ollamaProcess.kill();
    }
}
//# sourceMappingURL=extension.js.map