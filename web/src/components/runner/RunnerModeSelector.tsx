import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Database, BarChart3, Shield, Play, Loader2 } from "lucide-react";
import DatasetUpload from "@/components/DatasetUpload";

interface RunnerModeSelectorProps {
    activeTab: string;
    setActiveTab: (v: string) => void;
    datasetPath: string;
    setDatasetPath: (v: string) => void;
    datasets: { name: string; path: string }[];
    handleUploadSuccess: (filePath: string) => void;
    handleRun: () => void;
    status: string;
}

export const RunnerModeSelector: React.FC<RunnerModeSelectorProps> = ({
    activeTab, setActiveTab, datasetPath, setDatasetPath, datasets,
    handleUploadSuccess, handleRun, status
}) => {
    const labelClasses = "text-xs font-semibold text-[#45515e] uppercase tracking-wider mb-2 flex items-center gap-2";

    return (
        <Card className="bg-white border border-[#e5e7eb] shadow-[rgba(0,0,0,0.08)_0px_4px_6px] rounded-xl overflow-hidden relative">
            <CardHeader className="pb-4">
                <CardTitle className="text-lg font-bold tracking-tight text-[#222222] z-10 flex items-center gap-2">
                    Режим работы
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5 z-10 relative">
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList className="w-full bg-[#f2f3f5] border border-[#e5e7eb] p-1 rounded-md">
                        <TabsTrigger value="eval" className="flex-1 gap-1.5 text-sm">
                            <BarChart3 className="w-3.5 h-3.5" />
                            Evaluate RAG
                        </TabsTrigger>
                        <TabsTrigger value="redteam" className="flex-1 gap-1.5 text-sm">
                            <Shield className="w-3.5 h-3.5" />
                            Red Teaming
                        </TabsTrigger>
                    </TabsList>

                    {/* Evaluate RAG - Dataset Selection */}
                    <TabsContent value="eval" className="space-y-4 mt-4">
                        <div className="space-y-3">
                            <div>
                                <label className={labelClasses}><Database className="w-3.5 h-3.5 text-emerald-400" /> Загрузить новый датасет</label>
                                <DatasetUpload onUploadSuccess={handleUploadSuccess} />
                            </div>

                            <div className="relative py-1">
                                <div className="absolute inset-0 flex items-center">
                                    <div className="w-full border-t border-[#e5e7eb]"></div>
                                </div>
                                <div className="relative flex justify-center text-xs">
                                    <span className="bg-white px-3 py-1 text-[#8e8e93] rounded-full text-[10px]">или выберите существующий</span>
                                </div>
                            </div>

                            <div>
                                <label className={labelClasses}><Database className="w-3.5 h-3.5 text-emerald-400" /> Выбор датасета</label>
                                <Select value={datasetPath} onValueChange={(v) => v && setDatasetPath(v)}>
                                    <SelectTrigger className="bg-white border border-[#e5e7eb] text-[#222222] h-9 w-full focus:ring-[#1456f0]/30 text-sm rounded-md">
                                        <SelectValue placeholder="Загрузка..." />
                                    </SelectTrigger>
                                    <SelectContent className="bg-white border-[#e5e7eb] text-[#222222]">
                                        {datasets.map(d => (
                                            <SelectItem key={d.path} value={d.path}>{d.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </TabsContent>

                    {/* Red Teaming - No dataset needed */}
                    <TabsContent value="redteam" className="space-y-4 mt-4">
                        <div className="p-4 rounded-lg bg-[#fef2f2] border border-[#fecaca]">
                            <div className="flex items-start gap-2">
                                <Shield className="w-4 h-4 text-[#dc2626] mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-[#dc2626]">Red Teaming режим</p>
                                    <p className="text-xs text-[#8e8e93] mt-1">Атаки генерируются автоматически. Настройки доступны слева.</p>
                                </div>
                            </div>
                        </div>
                    </TabsContent>
                </Tabs>

                <div className="pt-4 border-t border-[#e5e7eb]">
                    <button
                        onClick={handleRun}
                        disabled={status === 'loading'}
                        className="w-full flex items-center justify-center gap-2 bg-[#1456f0] hover:bg-[#0d47d1] text-white font-semibold py-3 px-4 rounded-lg shadow-lg shadow-[#1456f0]/20 hover:shadow-xl hover:shadow-[#1456f0]/30 transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed tracking-wide text-sm"
                    >
                        {status === 'loading' ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Play className="w-5 h-5" />
                        )}
                        {activeTab === "eval" ? "Запустить Evaluation" : "Запустить Red Team"}
                    </button>
                </div>
            </CardContent>
        </Card>
    );
};
