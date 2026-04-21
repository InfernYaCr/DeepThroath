import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { BarChart3 } from "lucide-react";

interface EvalConfigPanelProps {
    judges: { name: string; model: string; provider: string }[];
    evalJudge: string;
    setEvalJudge: (v: string) => void;
    limit: string;
    setLimit: (v: string) => void;
    workers: string;
    setWorkers: (v: string) => void;
    metrics: { AR: boolean; FA: boolean; CP: boolean; CR: boolean };
    setMetrics: (v: any) => void;
    thresholds: { AR: string; FA: string; CP: string; CR: string };
    setThresholds: (v: any) => void;
}

export const EvalConfigPanel: React.FC<EvalConfigPanelProps> = ({
    judges, evalJudge, setEvalJudge, limit, setLimit, workers, setWorkers,
    metrics, setMetrics, thresholds, setThresholds
}) => {
    const inputClasses = "flex h-9 w-full rounded-md border border-[#e5e7eb] bg-white px-3 py-2 text-sm text-[#222222] placeholder:text-[#8e8e93] focus:outline-none focus:ring-2 focus:ring-[#1456f0]/30 focus:border-[#1456f0] transition-all";
    const labelClasses = "text-xs font-semibold text-[#45515e] uppercase tracking-wider mb-2 flex items-center gap-2";

    return (
        <Card className="bg-white border border-[#e5e7eb] shadow-[rgba(0,0,0,0.08)_0px_4px_6px] rounded-xl overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-5">
                <BarChart3 className="w-24 h-24 text-[#1456f0]" />
            </div>
            <CardHeader className="pb-4">
                <CardTitle className="text-lg font-bold tracking-tight text-[#222222] z-10 flex justify-between items-center">
                    <span className="flex items-center gap-2">
                        Настройки Evaluation
                    </span>
                    <Badge variant="outline" className="bg-[#eff6ff] text-[#2563eb] border-[#bfdbfe] px-2 py-0.5 text-xs">RAG Quality</Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 z-10 relative">
                <div>
                    <label className={labelClasses}>ID Модели-судьи (Judge Target)</label>
                    <Select value={evalJudge} onValueChange={(v) => v && setEvalJudge(v)}>
                        <SelectTrigger className="bg-white border border-[#e5e7eb] text-[#222222] h-9 w-full focus:ring-[#1456f0]/30 rounded-md">
                            <SelectValue placeholder="Выберите модель-судью..." />
                        </SelectTrigger>
                        <SelectContent className="bg-white border-[#e5e7eb] text-[#222222]">
                            {judges.map(judge => (
                                <SelectItem key={judge.name} value={judge.name}>
                                    {judge.name} ({judge.provider}: {judge.model})
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <p className="text-xs text-[#8e8e93] mt-1">Определено в eval/config/targets.yaml</p>
                </div>

                <div>
                    <label className={labelClasses}>Ограничение (Limit)</label>
                    <input
                        type="number"
                        className={inputClasses}
                        value={limit}
                        onChange={e => setLimit(e.target.value)}
                        placeholder="Например, 5 (оставить пустым для всего)"
                    />
                </div>

                <div>
                    <label className={labelClasses}>Параллельные воркеры (Workers)</label>
                    <input
                        type="number"
                        className={inputClasses}
                        value={workers}
                        onChange={e => setWorkers(e.target.value)}
                        placeholder="4"
                        min="1"
                        max="16"
                    />
                    <p className="text-xs text-[#8e8e93] mt-1">Количество одновременных запросов к API (1-16)</p>
                </div>

                <div>
                    <label className={labelClasses}>Что вычислять (Метрики и пороги)</label>
                    <div className="space-y-3">
                        {/* Категория: Генерация */}
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Badge variant="outline" className="bg-[#eff6ff] text-[#2563eb] border-[#bfdbfe] px-2 py-0.5 text-[10px] font-semibold">Генерация</Badge>
                            </div>
                            <div className="space-y-2 pl-2">
                                {(["AR", "FA"] as const).map(m => (
                                    <div key={m} className="space-y-1.5">
                                        <label className="flex items-center gap-2 text-sm text-[#222222] select-none cursor-pointer p-2 rounded-md border border-[#e5e7eb] bg-white hover:bg-[#f2f3f5] hover:border-[#d1d5db] transition-all">
                                            <input
                                                type="checkbox"
                                                className="w-3.5 h-3.5 rounded border-[#e5e7eb] text-blue-500 focus:ring-blue-500/50"
                                                checked={metrics[m]}
                                                onChange={e => setMetrics({ ...metrics, [m]: e.target.checked })}
                                            />
                                            <span className="font-medium text-xs flex-1">{m === "AR" ? "Answer Relevancy" : "Faithfulness"}</span>
                                        </label>
                                        {metrics[m] && (
                                            <div className="pl-6 flex items-center gap-2">
                                                <span className="text-[10px] text-[#8e8e93] uppercase tracking-wide">Порог:</span>
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    min="0"
                                                    max="1"
                                                    className="flex h-7 w-20 rounded-md border border-[#e5e7eb] bg-white px-2 py-1 text-xs text-[#222222] focus:outline-none focus:ring-1 focus:ring-[#1456f0]/30 focus:border-[#1456f0]"
                                                    value={thresholds[m]}
                                                    onChange={e => setThresholds({ ...thresholds, [m]: e.target.value })}
                                                />
                                                <span className="text-[10px] text-[#8e8e93]">{m === "AR" ? "(>0.80 хорошо)" : "(>0.90 хорошо)"}</span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Категория: Точность Retrieval */}
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Badge variant="outline" className="bg-[#ecfdf5] text-[#059669] border-[#a7f3d0] px-2 py-0.5 text-[10px] font-semibold">Точность Retrieval</Badge>
                            </div>
                            <div className="space-y-2 pl-2">
                                {(["CP", "CR"] as const).map(m => (
                                    <div key={m} className="space-y-1.5">
                                        <label className="flex items-center gap-2 text-sm text-[#222222] select-none cursor-pointer p-2 rounded-md border border-[#e5e7eb] bg-white hover:bg-[#f2f3f5] hover:border-[#d1d5db] transition-all">
                                            <input
                                                type="checkbox"
                                                className="w-3.5 h-3.5 rounded border-[#e5e7eb] text-emerald-500 focus:ring-emerald-500/50"
                                                checked={metrics[m]}
                                                onChange={e => setMetrics({ ...metrics, [m]: e.target.checked })}
                                            />
                                            <span className="font-medium text-xs flex-1">{m === "CP" ? "Context Precision" : "Context Recall"}</span>
                                        </label>
                                        {metrics[m] && (
                                            <div className="pl-6 flex items-center gap-2">
                                                <span className="text-[10px] text-[#8e8e93] uppercase tracking-wide">Порог:</span>
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    min="0"
                                                    max="1"
                                                    className="flex h-7 w-20 rounded-md border border-[#e5e7eb] bg-white px-2 py-1 text-xs text-[#222222] focus:outline-none focus:ring-1 focus:ring-[#1456f0]/30 focus:border-[#1456f0]"
                                                    value={thresholds[m]}
                                                    onChange={e => setThresholds({ ...thresholds, [m]: e.target.value })}
                                                />
                                                <span className="text-[10px] text-[#8e8e93]">{m === "CP" ? "(>0.70 хорошо)" : "(>0.75 хорошо)"}</span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
