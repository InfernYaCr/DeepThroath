import { NextResponse } from 'next/server';
import { execFile } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';

/**
 * GET /api/eval/export-pdf?scan=<scan_dir_name>&threshold=0.70
 *
 * Runs `python eval/export_pdf.py <results_dir>` as a subprocess,
 * writes the PDF to a temp file and streams it back to the client.
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

    // Write PDF to a temp file so we can stream it back
    const tmpPdf = path.join(os.tmpdir(), `rag_report_${Date.now()}.pdf`);
    const exportScript = path.join(projectRoot, 'eval', 'export_pdf.py');

    // Prefer: PYTHON_BIN env var → project venv → system python3
    const venvPython = path.join(projectRoot, '.venv', 'bin', 'python3');
    const python = process.env.PYTHON_BIN
        ?? (fs.existsSync(venvPython) ? venvPython : 'python3');

    const args = [exportScript, resultsDir, '--out', tmpPdf, `--fail-below=${threshold}`];

    try {
        await new Promise<void>((resolve, reject) => {
            execFile(python, args, { cwd: path.join(projectRoot, 'eval'), timeout: 60_000 },
                (err, stdout, stderr) => {
                    if (err) {
                        reject(new Error(stderr || err.message));
                    } else {
                        resolve();
                    }
                });
        });

        if (!fs.existsSync(tmpPdf)) {
            return NextResponse.json({ error: 'PDF generation failed (no output file)' }, { status: 500 });
        }

        const pdfBytes = fs.readFileSync(tmpPdf);
        fs.unlinkSync(tmpPdf);

        const fileName = `${scan}_report.pdf`;

        return new Response(pdfBytes, {
            headers: {
                'Content-Type': 'application/pdf',
                'Content-Disposition': `attachment; filename="${fileName}"`,
                'Content-Length': String(pdfBytes.length),
            },
        });
    } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        return NextResponse.json({ error: `PDF export failed: ${msg}` }, { status: 500 });
    }
}
