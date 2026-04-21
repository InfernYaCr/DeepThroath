import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield } from "lucide-react";

interface RedTeamConfigPanelProps {
    redteamJudge: string;
    setRedteamJudge: (v: string) => void;
    attacksPerVuln: string;
    setAttacksPerVuln: (v: string) => void;
    threshold: string;
    setThreshold: (v: string) => void;
}

export const RedTeamConfigPanel: React.FC<RedTeamConfigPanelProps> = ({
    redteamJudge, setRedteamJudge, attacksPerVuln, setAttacksPerVuln, threshold, setThreshold
}) => {
    const inputClasses = "flex h-9 w-full rounded-md border border-[#e5e7eb] bg-white px-3 py-2 text-sm text-[#222222] placeholder:text-[#8e8e93] focus:outline-none focus:ring-2 focus:ring-[#1456f0]/30 focus:border-[#1456f0] transition-all";
    const labelClasses = "text-xs font-semibold text-[#45515e] uppercase tracking-wider mb-2 flex items-center gap-2";

    return (
        <Card className="bg-white border border-[#e5e7eb] shadow-[rgba(0,0,0,0.08)_0px_4px_6px] rounded-xl overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-5">
                <Shield className="w-24 h-24 text-[#dc2626]" />
            </div>
            <CardHeader className="pb-4">
                <CardTitle className="text-lg font-bold tracking-tight text-[#222222] z-10 flex justify-between items-center">
                    <span className="flex items-center gap-2">
                        Настройки Red Teaming
                    </span>
                    <Badge variant="outline" className="bg-[#fef2f2] text-[#dc2626] border-[#fecaca] px-2 py-0.5 text-xs">Security</Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 z-10 relative">
                <div>
                    <label className={labelClasses}>ID Модели-судьи (Judge Preset)</label>
                    <input
                        type="text"
                        className={inputClasses}
                        value={redteamJudge}
                        onChange={e => setRedteamJudge(e.target.value)}
                        placeholder="gpt-4o-mini"
                    />
                    <p className="text-xs text-[#8e8e93] mt-1">Пресеты: gpt-4o-mini, gemini-flash, haiku, llama3-70b</p>
                </div>

                <div>
                    <label className={labelClasses}>Атак на тип уязвимости (Attacks per Vuln)</label>
                    <input
                        type="number"
                        className={inputClasses}
                        value={attacksPerVuln}
                        onChange={e => setAttacksPerVuln(e.target.value)}
                        placeholder="1"
                        min="1"
                    />
                    <p className="text-xs text-[#8e8e93] mt-1">Количество симуляций атак на каждую уязвимость</p>
                </div>

                <div>
                    <label className={labelClasses}>Порог успеха атаки (ASR Threshold)</label>
                    <input
                        type="number"
                        step="0.01"
                        className={inputClasses}
                        value={threshold}
                        onChange={e => setThreshold(e.target.value)}
                        placeholder="0.20"
                        min="0"
                        max="1"
                    />
                    <p className="text-xs text-[#8e8e93] mt-1">Attack Success Rate выше порога = FAIL</p>
                </div>
            </CardContent>
        </Card>
    );
};
