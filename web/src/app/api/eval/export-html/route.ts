import { NextResponse } from 'next/server';
import { execFile } from 'child_process';
import path from 'path';
import fs from 'fs';

/**
 * GET /api/eval/export-html?scan=<scan_dir_name>&threshold=0.70
 *
 * Generates HTML report for RAG evaluation results.
 * Returns standalone HTML that can be opened in new window for printing.
 */
export async function GET(request: Request): Promise<Response> {
    const { searchParams } = new URL(request.url);
    const scan = searchParams.get('scan');
    const threshold = searchParams.get('threshold') ?? '0.70';

    if (!scan) {
        return NextResponse.json({ error: 'Missing scan param' }, { status: 400 });
    }

    // Resolve paths relative to project root
    let projectRoot = process.cwd();
    let evalResultsDir = path.join(projectRoot, 'eval', 'results');
    if (!fs.existsSync(evalResultsDir)) {
        evalResultsDir = path.join(projectRoot, '..', 'eval', 'results');
        projectRoot = path.join(projectRoot, '..');
    }

    const resultsDir = path.join(evalResultsDir, scan);
    if (!fs.existsSync(resultsDir)) {
        return NextResponse.json({ error: `Scan not found: ${scan}` }, { status: 404 });
    }

    const metricsFile = path.join(resultsDir, 'metrics.json');
    if (!fs.existsSync(metricsFile)) {
        return NextResponse.json({ error: 'metrics.json not found in scan dir' }, { status: 404 });
    }

    // Use Python script to generate HTML (not PDF)
    const exportScript = path.join(projectRoot, 'eval', 'export_html.py');

    // Prefer: PYTHON_BIN env var → project venv → system python3
    const venvPython = path.join(projectRoot, '.venv', 'bin', 'python3');
    const python = process.env.PYTHON_BIN
        ?? (fs.existsSync(venvPython) ? venvPython : 'python3');

    const args = [exportScript, resultsDir, `--fail-below=${threshold}`];

    try {
        const html = await new Promise<string>((resolve, reject) => {
            execFile(python, args, { cwd: path.join(projectRoot, 'eval'), timeout: 60_000, maxBuffer: 10 * 1024 * 1024 },
                (err, stdout, stderr) => {
                    if (err) {
                        reject(new Error(stderr || err.message));
                    } else {
                        resolve(stdout);
                    }
                });
        });

        if (!html || html.trim().length === 0) {
            return NextResponse.json({ error: 'HTML generation failed (empty output)' }, { status: 500 });
        }

        return new Response(html, {
            headers: {
                'Content-Type': 'text/html; charset=utf-8',
            },
        });
    } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        return NextResponse.json({ error: `HTML export failed: ${msg}` }, { status: 500 });
    }
}
