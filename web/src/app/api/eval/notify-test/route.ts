import { NextResponse } from 'next/server';
import { execFile } from 'child_process';
import path from 'path';
import fs from 'fs';

/**
 * POST /api/eval/notify-test
 *
 * Sends a test Telegram notification by running scripts/test_telegram.py.
 * Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment.
 */
export async function POST(): Promise<Response> {
    let projectRoot = process.cwd();
    const scriptCandidate1 = path.join(projectRoot, 'scripts', 'test_telegram.py');
    const scriptCandidate2 = path.join(projectRoot, '..', 'scripts', 'test_telegram.py');

    const script = fs.existsSync(scriptCandidate1) ? scriptCandidate1
        : fs.existsSync(scriptCandidate2) ? scriptCandidate2
        : null;

    if (!script) {
        return NextResponse.json({ error: 'test_telegram.py not found' }, { status: 500 });
    }

    const resolvedRoot = fs.existsSync(scriptCandidate1) ? projectRoot : path.join(projectRoot, '..');
    const venvPython = path.join(resolvedRoot, '.venv', 'bin', 'python3');
    const python = process.env.PYTHON_BIN
        ?? (fs.existsSync(venvPython) ? venvPython : 'python3');

    try {
        const output = await new Promise<string>((resolve, reject) => {
            execFile(python, [script], { timeout: 15_000, env: process.env },
                (err, stdout, stderr) => {
                    if (err) reject(new Error(stderr || stdout || err.message));
                    else resolve(stdout.trim());
                });
        });
        return NextResponse.json({ ok: true, message: output });
    } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        return NextResponse.json({ ok: false, error: msg }, { status: 500 });
    }
}
