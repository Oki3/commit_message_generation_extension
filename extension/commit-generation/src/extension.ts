// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { exec, execSync } from 'child_process';
import { stdout } from 'process';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	try {
		// Get path to repository
		const repoPath = path.resolve(__dirname, '../../../');

		// Check if `.venv` exists
        const venvPath = path.join(repoPath, '.venv');
        const activatePath = path.join(venvPath, 'bin', 'activate'); // Adjust for Windows: use `Scripts` instead of `bin`

        if (!fs.existsSync(venvPath)) {
            vscode.window.showErrorMessage('.venv not found in the repository. Please create a virtual environment.');
            return;
        }

        // Install requirements if needed
        const requirementsPath = path.join(repoPath, 'requirements.txt');
        if (fs.existsSync(requirementsPath)) {
            const installCommand = `source ${activatePath} && pip install -r ${requirementsPath}`;
            execSync(installCommand, { cwd: repoPath, encoding: 'utf8', shell: '/bin/bash' });
            vscode.window.showInformationMessage('Installed Python requirements.');
        }

		// Capture the current diff
		const gitDiff = execSync('git diff --cached', { cwd: repoPath, encoding: 'utf8', shell: '/bin/bash' });


		if (!gitDiff.trim()) {
			vscode.window.showWarningMessage('No staged changes found.');
			return;
		}

		// Save the diff to a temporary file
		const tempDir = context.globalStorageUri.fsPath;
		if (!fs.existsSync(tempDir)) {
			fs.mkdirSync(tempDir, { recursive: true });
		}
		const tempFilePath = path.join(tempDir, 'staged_diff.txt');
		fs.writeFileSync(tempFilePath, gitDiff);
		
		// Run the Python script with the temp file as input
		const pythonScript = `python src/main.py --model mistral --prompt fewshot --diff_file "${tempFilePath}"`; 
		// TODO: update main to handle temp git diff file
		// const pythonScript = `python3 main.py --model mistral --prompt fewshot --sequential --input_file ${tempFilePath}`; 

		const options = { cwd: repoPath };
		
		exec(pythonScript, options, (error, stdout, stderr) => {
			if (error) {
				vscode.window.showErrorMessage(`Error: ${error.message}`);
				return;
			}
			if (stderr) {
				vscode.window.showErrorMessage(`Stderr: ${stderr}`);
				return;
			}
			vscode.window.showInformationMessage(`Output: ${stdout}`);
		});
		const commitMessage=stdout.toString().trim();
		vscode.window.showInputBox({
			value:commitMessage,
			prompt:'Review and edit the generated commit message, then press Enter to confirm.',
		}).then(
			userMessage=>{
				if(userMessage){
					try{
						const commitCommand='git commit -m ${userMessage}'
						execSync(commitCommand, { cwd: repoPath, shell: '/bin/bash' })
						vscode.window.showInformationMessage('Commit message applied successfully.');
					}
					catch(commitError)
					{
						if (commitError instanceof Error)
						{
							vscode.window.showErrorMessage(`Error committing changes: ${commitError.message}`);
						}
						else {
							vscode.window.showErrorMessage('An unknown error occurred while committing changes.');
						}
						
					}
				}
			    else{
					vscode.window.showWarningMessage('Commit message generation cancelled.');
				}

			}
		)
		
	} catch (error: unknown) {
		if (error instanceof Error) {
			vscode.window.showErrorMessage(`Failed to get diff: ${error.message}`);
		} else {
			vscode.window.showErrorMessage('Failed to get diff: Unknown error occurred.');
		}
	}
	   

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	const disposable = vscode.commands.registerCommand('commit-generation.generateMessage', () => {
		// The code you place here will be executed every time your command is executed
		// Display a message box to the user
		vscode.window.showInformationMessage('Hello World from Commit Generation!');
	});

	context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
