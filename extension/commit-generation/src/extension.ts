// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { exec, execSync } from 'child_process';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	try {
		// Get path to repository
		const repoPath = path.resolve(__dirname, '../../../');

		// Capture the current diff
		const gitDiff = execSync('git diff', { cwd: repoPath, encoding: 'utf8', shell: '/bin/bash' });


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

		// Temporary git diff logging
		console.log("Read Data: " + fs.readFileSync(tempFilePath, 'utf8'));
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
