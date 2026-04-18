import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

interface ScanEntry {
    label: string;
    value: string;
    timestamp: number;
}

/**
 * Parse RAGAS folder name: 20260418_130046_..._ragas
 * Returns human label: "18.04.2026 13:00  ·  exp_top_k_10"
 */
function parseScanLabel(name: string): string {
    const clean = name.replace(/_ragas$/, '');
    const m = clean.match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})\d{2}_(.+)$/);
    if (m) {
        const [, y, mo, d, hh, mm, rest] = m;
        const expName = rest.replace(/^(\d{8}_\d{6}_)+/, '');
        return `${d}.${mo}.${y} ${hh}:${mm}  ·  ${expName}`;
    }
    return name;
}

function resolveResultsDir(): string | null {
    const cwd = process.cwd();
    const candidates = [
        path.join(cwd, 'eval', 'results'),
        path.join(cwd, '..', 'eval', 'results'),
    ];
    return candidates.find(fs.existsSync) ?? null;
}

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const scanFile = searchParams.get('scanFile');

    const evalResultsDir = resolveResultsDir();
    if (!evalResultsDir) {
        return NextResponse.json(
            { error: 'Папка eval/results не найдена', metrics: [], allScans: [] },
            { status: 404 }
        );
    }

    const entries = fs.readdirSync(evalResultsDir, { withFileTypes: true });

    const scans: ScanEntry[] = entries
        .filter(e => e.isDirectory() && e.name.endsWith('_ragas'))
        .flatMap(d => {
            const metricPath = path.join(evalResultsDir, d.name, 'metrics.json');
            if (!fs.existsSync(metricPath)) return [];
            return [{
                label: parseScanLabel(d.name),
                value: d.name,
                timestamp: fs.statSync(metricPath).mtimeMs,
            }];
        })
        .sort((a, b) => b.timestamp - a.timestamp);

    const selectedValue =
        scanFile && scanFile !== 'latest' ? scanFile : (scans[0]?.value ?? null);

    if (!selectedValue) {
        return NextResponse.json(
            { error: 'Нет RAGAS-прогонов в eval/results/', metrics: [], allScans: [] },
            { status: 404 }
        );
    }

    const targetPath = path.join(evalResultsDir, selectedValue, 'metrics.json');

    if (!fs.existsSync(targetPath)) {
        return NextResponse.json(
            { error: `Файл не найден: ${targetPath}`, metrics: [], allScans: scans },
            { status: 404 }
        );
    }

    try {
        const metrics = JSON.parse(fs.readFileSync(targetPath, 'utf-8'));
        return NextResponse.json({ metrics, allScans: scans });
    } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        return NextResponse.json(
            { error: `Ошибка чтения JSON: ${msg}`, metrics: [], allScans: scans },
            { status: 500 }
        );
    }
}
