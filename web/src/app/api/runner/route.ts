import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';
import { randomUUID } from 'crypto';

export async function POST(req: Request) {
    try {
        const body = await req.json();
        
        // Обязательные параметры
        if (!body.api_contract || !body.dataset_path) {
            return NextResponse.json({ error: "Missing api_contract or dataset_path" }, { status: 400 });
        }

        // Мы запускаемся из web/, поэтому корень на один уровень выше
        const projectRoot = path.resolve(process.cwd(), '..');
        
        // Создаем временный конфигурационный файл API Contract
        const tmpConfigName = `.tmp_api_config_${randomUUID()}.json`;
        const tmpConfigPath = path.join(projectRoot, tmpConfigName);

        await fs.writeFile(tmpConfigPath, JSON.stringify(body.api_contract, null, 2), 'utf-8');

        // Подготавливаем вызов
        const pythonExecutable = path.join(projectRoot, '.venv', 'bin', 'python');
        const scriptPath = path.join(projectRoot, 'eval', 'scripts', 'run_eval.py');
        const inputPath = path.join(projectRoot, body.dataset_path);

        const args = [
            scriptPath,
            '--input', inputPath,
            '--dynamic-api-config', tmpConfigPath
        ];

        if (body.judge) {
            args.push('--judge', body.judge);
        }
        if (body.limit) {
            args.push('--limit', body.limit.toString());
        }

        console.log(`>>> Starting dynamic pipeline: ${pythonExecutable} ${args.join(' ')}`);

        // Запуск в отсоединенном (фоновом) режиме асинхронно
        const p = spawn(pythonExecutable, args, { cwd: projectRoot });

        p.on('exit', async (code) => {
            console.log(`>>> Pipeline exited with code ${code}`);
            try {
                // Подчищаем временный контракт когда процесс завершен
                await fs.unlink(tmpConfigPath);
            } catch (e) {
                console.error("Failed to delete temp config", e);
            }
        });

        // Направляем логи в консоль дашборда
        p.stdout.on('data', (d) => process.stdout.write(d.toString()));
        p.stderr.on('data', (d) => process.stderr.write(d.toString()));

        return NextResponse.json({
            success: true,
            message: "Pipeline successfully spawned",
            job_id: tmpConfigName,
        });

    } catch (e: any) {
        return NextResponse.json({ error: e.message || "Unknown error" }, { status: 500 });
    }
}
