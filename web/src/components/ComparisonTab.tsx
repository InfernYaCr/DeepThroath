"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function ComparisonTab({ allScans }: { allScans: {label: string, value: string}[] }) {
  const [scanA, setScanA] = useState<string>(allScans[1]?.value || allScans[0]?.value);
  const [scanB, setScanB] = useState<string>(allScans[0]?.value);
  const [dataA, setDataA] = useState<any[] | null>(null);
  const [dataB, setDataB] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!scanA || !scanB) return;
    setLoading(true);
    
    Promise.all([
      fetch("/api/data?scanFile=" + scanA).then(r => r.json()),
      fetch("/api/data?scanFile=" + scanB).then(r => r.json())
    ])
    .then(([resA, resB]) => {
      setDataA(resA.scanData || []);
      setDataB(resB.scanData || []);
      setLoading(false);
    })
    .catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [scanA, scanB]);

  if (allScans.length < 2) {
      return (
          <Card className="bg-slate-900 border-slate-800 text-center py-12">
             <CardContent>
                 <p className="text-slate-400">Для сравнения нужно минимум 2 скана. Запустите ещё один скан и вернитесь.</p>
             </CardContent>
          </Card>
      );
  }

  // Calculate Deltas
  const rows: any[] = [];
  let improvedCount = 0;
  let worsenedCount = 0;
  let unchangedCount = 0;

  if (dataA && dataB) {
      const mapA: Record<string, number> = {};
      dataA.forEach(r => mapA[r.vulnerability] = r.asr);
      
      const mapB: Record<string, number> = {};
      dataB.forEach(r => mapB[r.vulnerability] = r.asr);

      const allVulns = Array.from(new Set([...Object.keys(mapA), ...Object.keys(mapB)])).sort();

      allVulns.forEach(v => {
          const asrA = mapA[v] !== undefined ? mapA[v] : null;
          const asrB = mapB[v] !== undefined ? mapB[v] : null;
          
          let delta = null;
          let trend = "";
          let badgeVariant: "default" | "secondary" | "destructive" | "outline" = "outline";

          if (asrA !== null && asrB !== null) {
              delta = asrB - asrA;
              if (delta < -0.01) {
                  trend = "✅ Улучшилось";
                  improvedCount++;
                  badgeVariant = "default"; // green
              } else if (delta > 0.01) {
                  trend = "🔴 Ухудшилось";
                  worsenedCount++;
                  badgeVariant = "destructive";
              } else {
                  trend = "➡️ Без изменений";
                  unchangedCount++;
                  badgeVariant = "secondary";
              }
          } else if (asrA === null) {
              trend = "🆕 Новый тест";
              badgeVariant = "outline";
          } else {
              trend = "➖ Отсутствует в B";
              badgeVariant = "outline";
          }

          rows.push({
              vulnerability: v,
              asrA,
              asrB,
              delta,
              trend,
              badgeVariant
          });
      });
  }

  return (
    <div className="space-y-6">
       <div className="flex flex-col md:flex-row gap-6">
           <div className="flex-1 space-y-2">
               <label className="text-sm font-medium text-slate-400">Скан A (базовый)</label>
               <Select value={scanA} onValueChange={(val) => val && setScanA(val)}>
                 <SelectTrigger className="bg-slate-900 border-slate-800 text-slate-200">
                   <SelectValue placeholder="Выберите базовый скан" />
                 </SelectTrigger>
                 <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                   {allScans.map(scan => (
                     <SelectItem key={scan.value} value={scan.value}>{scan.label}</SelectItem>
                   ))}
                 </SelectContent>
               </Select>
           </div>
           
           <div className="flex-1 space-y-2">
               <label className="text-sm font-medium text-slate-400">Скан B (новый)</label>
               <Select value={scanB} onValueChange={(val) => val && setScanB(val)}>
                 <SelectTrigger className="bg-slate-900 border-slate-800 border-l-cyan-500 text-slate-200">
                   <SelectValue placeholder="Выберите новый скан" />
                 </SelectTrigger>
                 <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                   {allScans.map(scan => (
                     <SelectItem key={scan.value} value={scan.value}>{scan.label}</SelectItem>
                   ))}
                 </SelectContent>
               </Select>
           </div>
       </div>

       {loading && <div className="py-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-slate-500" /></div>}

       {!loading && dataA && dataB && (
         <>
             <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-slate-900/50 border-emerald-900/50">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-emerald-400 text-sm font-medium">Улучшилось</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold text-slate-100">{improvedCount}</div>
                    </CardContent>
                </Card>
                <Card className="bg-slate-900/50 border-red-900/50">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-red-400 text-sm font-medium">Ухудшилось</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold text-slate-100">{worsenedCount}</div>
                    </CardContent>
                </Card>
                <Card className="bg-slate-900/50 border-slate-800/50">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-slate-400 text-sm font-medium">Без изменений</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold text-slate-100">{unchangedCount}</div>
                    </CardContent>
                </Card>
             </div>

             <div className="rounded-md border border-slate-800">
                  <Table>
                    <TableHeader className="bg-slate-950">
                      <TableRow className="border-slate-800">
                        <TableHead>Уязвимость</TableHead>
                        <TableHead>ASR (Скан A)</TableHead>
                        <TableHead>ASR (Скан B)</TableHead>
                        <TableHead>Δ Разница</TableHead>
                        <TableHead>Итог</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                        {rows.map((row, i) => (
                             <TableRow key={i} className="border-slate-800 hover:bg-slate-900/50">
                                <TableCell className="font-medium">{row.vulnerability}</TableCell>
                                <TableCell className="text-slate-400">{row.asrA !== null ? (row.asrA * 100).toFixed(1) + "%" : "—"}</TableCell>
                                <TableCell className="text-slate-300 font-semibold">{row.asrB !== null ? (row.asrB * 100).toFixed(1) + "%" : "—"}</TableCell>
                                <TableCell className={row.delta !== null ? (row.delta > 0 ? 'text-red-400' : (row.delta < 0 ? 'text-emerald-400' : 'text-slate-500')) : 'text-slate-500'}>
                                    {row.delta !== null ? (row.delta > 0 ? "+" : "") + (row.delta * 100).toFixed(1) + "%" : "—"}
                                </TableCell>
                                <TableCell>
                                    <Badge variant={row.badgeVariant as any} className={row.badgeVariant === "default" ? "bg-emerald-900/80 text-emerald-400 hover:bg-emerald-900" : (row.badgeVariant === "destructive" ? "bg-red-900/80 text-red-400" : "")}>{row.trend}</Badge>
                                </TableCell>
                             </TableRow>
                        ))}
                    </TableBody>
                  </Table>
             </div>
         </>
       )}
    </div>
  );
}
