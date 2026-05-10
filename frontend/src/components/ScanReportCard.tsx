import { FileText, ChevronRight, AlertCircle, CheckCircle2 } from "lucide-react";
import type { ScanTask, ScanError } from "../types";
import { Card } from "./ui/Card";
import { Button } from "./ui/Button";

export interface ScanReportCardProps {
  task: ScanTask;
  errorData?: { items: ScanError[] } | null;
  onLoadErrors: () => void;
}

export function ScanReportCard({ task, errorData, onLoadErrors }: ScanReportCardProps) {
  return (
    <Card className="p-8">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <FileText className="w-5 h-5 text-slate-400" />
          扫描报告
        </h3>
        {task.failed_files > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onLoadErrors}
            className="text-blue-600 hover:text-blue-700"
          >
            加载错误日志
            <ChevronRight className="w-4 h-4" />
          </Button>
        )}
      </div>

      {errorData?.items?.length ? (
        <div className="space-y-3 mt-4">
          {errorData.items.map((e, i) => (
            <div key={i} className="text-sm text-rose-700 bg-rose-50/50 rounded-xl p-4 border border-rose-100">
              <div className="font-semibold mb-1 break-all flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                {e.file_path}
              </div>
              <div className="text-rose-600/80 ml-6">{e.error_message}</div>
            </div>
          ))}
        </div>
      ) : task.failed_files > 0 ? (
        <p className="text-slate-500 text-sm mt-2">点击上方按钮加载错误详情...</p>
      ) : (
        <div className="flex flex-col items-center justify-center py-6 text-slate-500">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mb-3 opacity-50" />
          <p className="text-sm font-medium">太棒了，没有任何扫描错误！</p>
        </div>
      )}
    </Card>
  );
}