import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

export async function POST(request: Request) {
  try {
    const projectRoot = path.join(process.cwd(), '..');
    
    // We start the python process using the virtual environment if possible
    const venvPythonPath = path.join(projectRoot, '.venv', 'bin', 'python');
    const pythonExe = fs.existsSync(venvPythonPath) ? venvPythonPath : 'python';

    return new Promise((resolve) => {
        const pythonProcess = spawn(pythonExe, ['scripts/run_redteam.py'], {
            cwd: projectRoot,
        });

        let output = "";

        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            output += data.toString();
        });

        pythonProcess.on('close', (code) => {
            resolve(NextResponse.json({ success: code === 0, output, code }));
        });
    });

  } catch (error: any) {
    console.error("API Error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
