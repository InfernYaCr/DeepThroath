import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

export async function GET() {
    try {
        const projectRoot = path.resolve(process.cwd(), '..');
        const datasetsDir = path.join(projectRoot, 'eval', 'datasets');
        
        let files: string[] = [];
        try {
            files = await fs.readdir(datasetsDir);
        } catch (e) {
            console.log("No datasets dir or error:", e);
        }

        const jsonFiles = files
            .filter(f => f.endsWith('.json'))
            .map(f => ({
                name: f,
                path: `eval/datasets/${f}`
            }));

        return NextResponse.json({ datasets: jsonFiles });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 500 });
    }
}
