import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { spawn , ChildProcessWithoutNullStreams} from 'child_process';

let ollamaProcess: ChildProcessWithoutNullStreams | null = null;

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
                    { cwd: repoPath, stdio:'inherit' }
                );
                
                // installCmd.stderr.on('data', (data) => {
                //     vscode.window.showErrorMessage(`Pip error: ${data}`);
                // });
                
                installCmd.on('close', (code) => {
                    if (code !== 0) {
                        reject(new Error(`pip install failed. Exit code: ${code}`));
                    } else {
                        resolve();
                    }
                });
            });
        };
        
        async function startOllamaServer(repoPath: string):Promise<void>{
            return new Promise((resolve, reject) => {
                // 1) Spawn 'ollama serve'
                ollamaProcess = spawn('ollama', ['serve'], { cwd: repoPath});
                
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
        async function processFileChange(file: string): Promise<void> {
            return new Promise((resolve, reject) => {
                const repoPath = path.resolve(__dirname, '../../../');
                let fileDiff = '';
                const fileDiffProcess = spawn('git', ['diff', '--cached', '--', file], { cwd: repoPath });
                
                fileDiffProcess.stdout.on('data', (data) => {
                    fileDiff += data.toString();
                });
                
                fileDiffProcess.stderr.on('data', (err) => {
                    vscode.window.showErrorMessage(`Error getting diff for ${file}: ${err}`);
                });
                
                fileDiffProcess.on('close', async (code) => {
                    if (code !== 0) {
                        return reject(new Error(`git diff for ${file} failed with code ${code}`));
                    }
                    if (!fileDiff.trim()) {
                        return resolve(); // no changes for this file
                    }
                    
                    const fewShotExamples = [
                        'Fix null pointer exception in authentication',
                        'Refactor logging setup for better traceability',
                        'Improve API request handling to avoid timeouts'
                    ].join('\n');
                    
                    // Create a file-specific prompt
                    let prompt = `
            You are an AI assistant tasked with generating a concise one-sentence Git commit message for changes in a single file.
            Examples of relevant commit messages:
            ${fewShotExamples}
            File: ${file}
            Diff:
            ${fileDiff}
            Output:
           - A concise, one-sentence commit message describing the changes in the file, including the filename in the message if relevant. Limit to under 100 characters.`;
                    
                    // Spawn Python script for this prompt
                    const pyProcess = spawn(
                        venvPython,
                        ['src/runExtension.py', '--output_txt', 'my_messages.txt'],
                        { cwd: repoPath }
                    );
                    
                    let generatedMessageForFile = '';
                    
                    pyProcess.stdout.on('data', (data) => {
                        generatedMessageForFile += data.toString();
                    });
                    
                    pyProcess.stderr.on('data', (data) => {
                        console.error(`[Python stderr for ${file}]: ${data}`);
                    });
                    
                    pyProcess.on('close', async(pyCode) => {
                        if (pyCode !== 0) {
                            vscode.window.showErrorMessage(`Python script for ${file} exited with code ${pyCode}`);
                        } else {
                            const trimmedMessage = generatedMessageForFile.trim();
                            console.log(`Commit message for ${file}:`, trimmedMessage);
                            
                            // Save the file and its message
                            fileMessages.push({ file, message: trimmedMessage });
                            
                        }
                        resolve();
                    });
                    
                    // Pass prompt to Python script via stdin
                    pyProcess.stdin.write(prompt);
                    pyProcess.stdin.end();
                });
            });
        }
        let fileMessages: { file: string; message: string }[] = [];
        async function processChangedFiles(): Promise<void> {
            return new Promise((resolve, reject) => {
                const repoPath = path.resolve(__dirname, '../../../');
                const listFilesProcess = spawn('git', ['diff', '--name-only', '--cached'], { cwd: repoPath });
                let changedFiles: string[] = [];
                
                listFilesProcess.stdout.on('data', (data) => {
                    changedFiles.push(...data.toString().split('\n').filter((f: string) => f.trim()));
                });
                
                listFilesProcess.stderr.on('data', (errData) => {
                    vscode.window.showErrorMessage(`Error listing changed files: ${errData}`);
                });
                
                listFilesProcess.on('close', async (code) => {
                    if (code !== 0) {
                        return reject(new Error(`git diff --name-only exited with code ${code}`));
                    }
                    
                    for (const file of changedFiles) {
                        await processFileChange(file);
                    }
                    let options: { label: string; description?: string }[] = fileMessages.map(item => ({
                        label: `${item.file}: ${item.message}`
                    }));
                    
                    
                    // Add a bulk action option at the beginning of the options list
                    options.unshift({
                        label: '✅ Accept All',
                        description: 'Accept and copy all commit messages to clipboard'
                    });
                    
                    const selected = await vscode.window.showQuickPick(options, {
                        placeHolder: 'Review generated commit messages for each file or accept all.'
                    });
                    
                    if (!selected) {
                        vscode.window.showWarningMessage('No selection made.');
                        return resolve();
                    }
                    
                    if (selected.label === '✅ Accept All') {
                        // Concatenate all messages for the "Accept All" option
                        const allMessages = fileMessages
                        .map(item => `${item.file}: ${item.message}`)
                        .join('\n');
                        await vscode.env.clipboard.writeText(allMessages);
                        vscode.window.showInformationMessage('All commit messages copied to clipboard!');
                    } else {
                        // Handle individual file selection for accept/reject as before
                        const selectedFile = selected.label;
                        const selectedItem = fileMessages.find(item => item.file === selectedFile);
                        if (!selectedItem) {
                            vscode.window.showErrorMessage('Selected file not found.');
                            return resolve();
                        }
                        
                        const decisionOptions = [
                            { label: '✅ Accept', detail: selectedItem.message },
                            { label: '❌ Reject', detail: 'Do not use this commit message.' }
                        ];
                        
                        const decision = await vscode.window.showQuickPick(decisionOptions, {
                            placeHolder: `Review the commit message for ${selectedItem.file}:`
                        });
                        
                        if (decision?.label === '✅ Accept') {
                            await vscode.env.clipboard.writeText(selectedItem.message);
                            vscode.window.showInformationMessage(`Commit message for ${selectedItem.file} accepted and copied to clipboard!`);
                        } else if (decision?.label === '❌ Reject') {
                            vscode.window.showWarningMessage(`Commit message for ${selectedItem.file} rejected.`);
                        } else {
                            vscode.window.showWarningMessage('No action taken.');
                        }
                    }
                    resolve();
                });
            });
        }
        async function getChangedFiles(): Promise<string[]> {
            return new Promise((resolve, reject) => {
                const listFilesProcess = spawn('git', ['diff', '--name-only', '--cached'], { cwd: repoPath });
                let changedFiles: string[] = [];
                
                listFilesProcess.stdout.on('data', (data) => {
                    changedFiles.push(...data.toString().split('\n').filter((f: string) => f.trim()));
                });
                
                listFilesProcess.stderr.on('data', (errData) => {
                    vscode.window.showErrorMessage(`Error listing changed files: ${errData}`);
                });
                
                listFilesProcess.on('close', (code) => {
                    if (code !== 0) {
                        return reject(new Error(`git diff --name-only exited with code ${code}`));
                    }
                    resolve(changedFiles);
                });
            });
        }
        
        async function runPythonScriptWithPipedDiff(): Promise<void> {
            return new Promise((resolve, reject) => {
                generatedMessage = '';
                const fewShotExamples = [
                    'Fix null pointer exception, changed variable a to b and removed redundant lines in authentication',
                    'Refactor logging setup for better traceability',
                    'Improve API request handling to avoid timeouts'
                ].join('\n');
                
                let diffCollected = `
            You are an AI assistant designed to produce concise, descriptive commit messages for Git changes. 
           Below are up to three examples of commit messages that previously touched upon the same code or files. 
          Please note that the first example is more important and should influence your message the most. 
          Use the style and context of these examples, prioritizing the first examples, to inspire a new commit message for the provided Git diff.  
          Do not include references to issue numbers or pull requests.  Do not surround with quotes. Do not summarize. Point out specific changes in the code. 
          Examples of relevant commit messages:
          ${fewShotExamples}
         Now here is the new Git diff for which you must generate a commit message:
            `;
                
                // A) Spawn 'git diff --cached'
                const gitProcess = spawn('git', ['diff', '--cached'], { cwd: repoPath });
                
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
            Output:
           For each file change in the provided diff, produce a concise, one-sentence commit message.
           Format:
           - File: <filename>
           Commit Message: <message>
          Separate each file's message with a newline.`;
                    
                    // D) Now spawn Python
                    const pyProcess = spawn(
                        venvPython,
                        // for example: ['src/runExtension.py', '--output_txt', 'my_messages.txt']
                        // or any other arguments your script needs:
                        ['src/runExtension.py', '--output_txt', 'my_messages.txt'],
                        { cwd: repoPath }
                    );
                    
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
                    pyProcess.on('close', async(pyCode) => {
                        if (pyCode !== 0) {
                            reject(new Error(`Python script exited with code ${pyCode}`));
                        } else {
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
                            } else if (selection?.label === '❌ Reject') {
                                vscode.window.showWarningMessage('Commit message rejected.');
                            } else {
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
        const runPythonScript = async (scriptArgs: string[]) => {
            return new Promise<void>((resolve, reject) => {
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
                
                pythonProcess.on('close', async(code) => {
                    if (code !== 0) {
                        reject(new Error(`Python script exited with code ${code}`));
                    } else {
                        console.log(generatedMessage.trim())
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
            
            try {
                const changedFiles = await getChangedFiles();
                
                if (changedFiles.length === 0) {
                    vscode.window.showWarningMessage('No staged changes found.');
                }     else if (changedFiles.length === 1) {
                    console.log("Single file changed. Using runPythonScriptWithPipedDiff...");
                    await runPythonScriptWithPipedDiff();
                } else {
                    console.log("Multiple files changed. Processing each file separately...");
                    await processChangedFiles();
                }
            }   catch (error) {
                if (error instanceof Error) {
                    vscode.window.showErrorMessage(`Error processing diffs: ${error.message}`);
                } else {
                    vscode.window.showErrorMessage('Unknown error processing diffs.');
                }
            }
            
            
            
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
        vscode.window.showInformationMessage('Commit message generation is ongoing.');
    });
    
    context.subscriptions.push(disposable);
}

// Deactivate
export function deactivate() {
    if (ollamaProcess) {
        console.log('Stopping Ollama server...');
        ollamaProcess.kill();
    }
}
