import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Link2, Key, Braces } from "lucide-react";

interface ApiContractConfigProps {
    method: string;
    setMethod: (v: string) => void;
    url: string;
    setUrl: (v: string) => void;
    headersStr: string;
    setHeadersStr: (v: string) => void;
    bodyStr: string;
    setBodyStr: (v: string) => void;
    extractAnswer: string;
    setExtractAnswer: (v: string) => void;
    extractChunks: string;
    setExtractChunks: (v: string) => void;
}

export const ApiContractConfig: React.FC<ApiContractConfigProps> = ({
    method, setMethod, url, setUrl, headersStr, setHeadersStr, bodyStr, setBodyStr,
    extractAnswer, setExtractAnswer, extractChunks, setExtractChunks
}) => {
    const inputClasses = "flex h-9 w-full rounded-md border border-[#e5e7eb] bg-white px-3 py-2 text-sm text-[#222222] placeholder:text-[#8e8e93] focus:outline-none focus:ring-2 focus:ring-[#1456f0]/30 focus:border-[#1456f0] transition-all";
    const textareaClasses = "flex w-full rounded-md border border-[#e5e7eb] bg-white px-3 py-2 text-sm text-[#222222] placeholder:text-[#8e8e93] focus:outline-none focus:ring-2 focus:ring-[#1456f0]/30 focus:border-[#1456f0] transition-all font-mono min-h-[100px] resize-none";
    const labelClasses = "text-xs font-semibold text-[#45515e] uppercase tracking-wider mb-2 flex items-center gap-2";

    return (
        <div className="space-y-5">
            <Card className="bg-white border border-[#e5e7eb] shadow-[rgba(0,0,0,0.08)_0px_4px_6px] rounded-xl overflow-hidden relative">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                    <Link2 className="w-24 h-24 text-[#1456f0]" />
                </div>
                <CardHeader className="pb-4">
                    <CardTitle className="text-lg font-bold tracking-tight text-[#222222] flex justify-between items-center z-10">
                        <span className="flex items-center gap-2">
                            Конфигурация запроса
                        </span>
                        <Badge variant="outline" className="bg-[#eff6ff] text-[#2563eb] border-[#bfdbfe] px-2 py-0.5 text-xs">Network</Badge>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 z-10 relative">
                    <div className="flex gap-4">
                        <div className="w-32">
                            <label className={labelClasses}>Method</label>
                            <Select value={method} onValueChange={(v) => v && setMethod(v)}>
                                <SelectTrigger className="bg-white border border-[#e5e7eb] text-[#222222] h-9 w-full focus:ring-[#1456f0]/30 rounded-md">
                                    <SelectValue placeholder="Method" />
                                </SelectTrigger>
                                <SelectContent className="bg-white border-[#e5e7eb] text-[#222222]">
                                    <SelectItem value="POST">POST</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="flex-1">
                            <label className={labelClasses}>Endpoint (URL)</label>
                            <input
                                type="text"
                                className={inputClasses}
                                value={url}
                                onChange={e => setUrl(e.target.value)}
                                placeholder="https://api.example.com/v1/rag"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className={labelClasses}><Key className="w-4 h-4 text-purple-400" /> Headers (JSON)</label>
                            <textarea
                                className={textareaClasses}
                                value={headersStr}
                                onChange={e => setHeadersStr(e.target.value)}
                                spellCheck={false}
                            />
                        </div>
                        <div>
                            <label className={labelClasses}><Braces className="w-4 h-4 text-pink-400" /> Body Payload (JSON)</label>
                            <textarea
                                className={textareaClasses}
                                value={bodyStr}
                                onChange={e => setBodyStr(e.target.value)}
                                spellCheck={false}
                            />
                            <p className="text-xs text-[#8e8e93] mt-2">Доступные переменные: {`{{user_query}}`}, {`{{category}}`}</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-white border border-[#e5e7eb] shadow-[rgba(0,0,0,0.08)_0px_4px_6px] rounded-xl overflow-hidden relative">
                <CardHeader className="pb-4">
                    <CardTitle className="text-lg font-bold tracking-tight text-[#222222] z-10 flex justify-between items-center">
                        <span className="flex items-center gap-2">
                            Маппинг ответа
                        </span>
                        <Badge variant="outline" className="bg-[#fdf2f8] text-[#be185d] border-[#fbcfe8] px-2 py-0.5 text-xs">Parsing</Badge>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 z-10 relative">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className={labelClasses}>Путь до основного ответа (Answer Path)</label>
                            <input
                                type="text"
                                className={inputClasses}
                                value={extractAnswer}
                                onChange={e => setExtractAnswer(e.target.value)}
                                placeholder="data.answer"
                            />
                        </div>
                        <div>
                            <label className={labelClasses}>Путь до найденных чанков (Chunks Path)</label>
                            <input
                                type="text"
                                className={inputClasses}
                                value={extractChunks}
                                onChange={e => setExtractChunks(e.target.value)}
                                placeholder="data.retrieved_chunks"
                            />
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};
