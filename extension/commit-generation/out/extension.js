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
                const installCmd = (0, child_process_1.spawn)(venvPip, ['install', '-r', requirementsPath], { cwd: repoPath });
                installCmd.stderr.on('data', (data) => {
                    vscode.window.showErrorMessage(`Pip error: ${data}`);
                });
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
        // git diff
        const getGitDiff = async () => {
            return new Promise((resolve, reject) => {
                const gitDiffProcess = (0, child_process_1.spawn)('git', ['diff'], { cwd: repoPath });
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
                    }
                    else {
                        reject(new Error(`git diff exited with code ${code}`));
                    }
                });
            });
        };
        // Run the Python script from .venv
        const runPythonScript = async (scriptArgs) => {
            return new Promise((resolve, reject) => {
                // If your script is at `src/main.py`, we can call it directly with the venv Python
                const pythonProcess = (0, child_process_1.spawn)(venvPython, scriptArgs, { cwd: repoPath });
                // Gather stdout (for commit message, etc.)
                pythonProcess.stdout.on('data', (data) => {
                    vscode.window.showInformationMessage(`Output: ${data}`);
                    generatedMessage += data.toString();
                });
                pythonProcess.on('close', (code) => {
                    if (code !== 0) {
                        reject(new Error(`Python script exited with code ${code}`));
                    }
                    else {
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
            // 7.3 Optionally do `ollama pull mistral` or other commands
            //     (Again, you can spawn them by using `venvPython` / `venvPip` 
            //      or call them directly if they are not Python-based.)
            // 
            // const ollamaCmd = spawn('ollama', ['pull', 'mistral'], { cwd: repoPath });
            // ... handle stdout, stderr, and exit code ...
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
            console.log("Diff file is written to temp file, located at", tempFilePath, ", now running the model to generate messages....");
            // 7.7 Run the Python script inside the venv
            //     (assuming the script is `src/main.py --model mistral --prompt baseline`)
            //     You might need to pass the path to your tempFilePath as well if your Python script uses it.
            await runPythonScript(['src/main.py', '--model', 'mistral', '--prompt', 'baseline']);
            console.log("Message automatically copied to clipboard. Ctrl+V to paste it to places you wish.");
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
        vscode.window.showInformationMessage('Commit message generated and copied to clipboard!');
    });
    context.subscriptions.push(disposable);
}
// Deactivate
function deactivate() { }
//# sourceMappingURL=extension.js.map