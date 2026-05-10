import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getOperations, rollbackOperation } from "../../services/api";
import type { OperationLog } from "../../types";
import toast from "react-hot-toast";
import {
  History,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Loader2,
  FileBox,
  AlertCircle
} from "lucide-react";
import { twMerge } from "tailwind-merge";

export default function OperationHistoryPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["operations", page],
    queryFn: () => getOperations({ page, page_size: 50 }),
  });

  const rollbackMutation = useMutation({
    mutationFn: (id: number) => rollbackOperation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["operations"] });
      toast.success("成功撤销操作，文件已恢复原位！");
    },
    onError: (err) => {
      toast.error(`撤销失败: ${err.message}`);
    }
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 50)) : 1;

  return (
    <div className="max-w-6xl mx-auto animation-fade-in flex flex-col relative min-h-full">
      {/* 背景光晕 */}
      <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="mb-6 shrink-0 relative z-10">
        <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-400 tracking-tight pb-1">操作历史</h2>
        <p className="text-slate-500 mt-1 font-medium">查看最近对文件执行的整理操作，或一键撤销（回滚）意外移动的文件。</p>
      </div>

      <div className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 shadow-sm relative flex flex-col mb-8">
        {/* Table Header */}
        <div className="grid grid-cols-[1fr_minmax(120px,2fr)_minmax(120px,2fr)_100px_140px_100px] gap-4 items-center px-6 py-4 border-b border-slate-100/80 bg-slate-50/40 sticky top-0 z-10 text-sm font-semibold text-slate-600 rounded-t-2xl">
          <div className="pl-2">操作类型</div>
          <div>源路径</div>
          <div>目标路径</div>
          <div className="text-center">状态</div>
          <div className="text-center">执行时间</div>
          <div className="text-right pr-2">操作</div>
        </div>

        {/* Table Body */}
        <div className="p-2">
          {isLoading ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-3 py-20">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p>加载历史记录中...</p>
            </div>
          ) : data?.items?.length ? (
            <div className="divide-y divide-slate-100/60">
              {data.items.map((o: OperationLog) => (
                <div key={o.id} className="grid grid-cols-[1fr_minmax(120px,2fr)_minmax(120px,2fr)_100px_140px_100px] gap-4 items-center px-6 py-3.5 hover:bg-slate-50/50 transition-colors group">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className={twMerge("p-1.5 rounded-lg shrink-0", operationIconBg(o.operation_type))}>
                      {operationIcon(o.operation_type)}
                    </div>
                    <span className="text-sm font-semibold text-slate-700 capitalize tracking-wide truncate">
                      {o.operation_type}
                    </span>
                  </div>

                  <div className="min-w-0 flex items-center gap-2">
                    <FileBox className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="text-sm text-slate-600 truncate font-medium" title={o.source_path}>
                      {o.source_path}
                    </span>
                  </div>

                  <div className="min-w-0 flex items-center gap-2">
                    <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />
                    <span className="text-sm text-slate-600 truncate font-medium" title={o.target_path ?? ""}>
                      {o.target_path ?? "-"}
                    </span>
                  </div>

                  <div className="flex justify-center">
                    <span className={twMerge("px-2.5 py-1 rounded-lg text-xs font-semibold border flex w-fit items-center gap-1.5", statusBadge(o.status))}>
                      {statusIcon(o.status)}
                      {statusText(o.status)}
                    </span>
                  </div>

                  <div className="text-xs text-slate-500 flex items-center justify-center gap-1.5 font-medium tabular-nums">
                    <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    {o.executed_at ? o.executed_at.slice(5, 16).replace("T", " ") : "-"}
                  </div>

                  <div className="text-right pr-1">
                    {o.rollback_available && o.status === "success" ? (
                      <button
                        onClick={() => rollbackMutation.mutate(o.id)}
                        disabled={rollbackMutation.isPending && rollbackMutation.variables === o.id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-700 border border-amber-200/60 rounded-lg text-xs font-semibold shadow-sm hover:bg-amber-100 hover:shadow disabled:opacity-50 disabled:pointer-events-none transition-all"
                      >
                        {rollbackMutation.isPending && rollbackMutation.variables === o.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <RotateCcw className="w-3.5 h-3.5" />
                        )}
                        撤销
                      </button>
                    ) : (
                      <span className="text-xs font-medium text-slate-400 select-none">-</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20">
              <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                <History className="w-8 h-8 text-slate-300" />
              </div>
              <p className="font-medium text-slate-500">没有任何操作历史</p>
              <p className="text-sm mt-1">您可以先前往“整理建议”中执行一些移动操作</p>
            </div>
          )}
        </div>

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
            <span className="text-sm text-slate-500 font-medium">
              共 {data?.total ?? 0} 条记录
            </span>
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-500">
                <strong className="text-slate-700">{page}</strong> / {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 font-medium text-sm hover:bg-slate-50 shadow-sm disabled:opacity-40 disabled:hover:bg-white transition-colors"
                >
                  上一页
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 font-medium text-sm hover:bg-slate-50 shadow-sm disabled:opacity-40 disabled:hover:bg-white transition-colors"
                >
                  下一页
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function operationIcon(type: string) {
  if (type === "rollback") return <RotateCcw className="w-4 h-4" />;
  return <ArrowRight className="w-4 h-4" />;
}

function operationIconBg(type: string): string {
  if (type === "rollback") return "bg-amber-100 text-amber-600";
  return "bg-blue-100 text-blue-600";
}

function statusText(status: string): string {
  switch (status) {
    case "success": return "成功";
    case "failed": return "失败";
    case "rolled_back": return "已撤销";
    case "pending": return "执行中";
    default: return status;
  }
}

function statusIcon(status: string) {
  switch (status) {
    case "success": return <CheckCircle2 className="w-3.5 h-3.5" />;
    case "failed": return <XCircle className="w-3.5 h-3.5" />;
    case "rolled_back": return <RotateCcw className="w-3.5 h-3.5" />;
    case "pending": return <Loader2 className="w-3.5 h-3.5 animate-spin" />;
    default: return <AlertCircle className="w-3.5 h-3.5" />;
  }
}

function statusBadge(status: string): string {
  switch (status) {
    case "success": return "bg-emerald-50 text-emerald-700 border-emerald-200/60";
    case "failed": return "bg-rose-50 text-rose-700 border-rose-200/60";
    case "rolled_back": return "bg-slate-100 text-slate-500 border-slate-200/60 line-through";
    case "pending": return "bg-blue-50 text-blue-700 border-blue-200/60";
    default: return "bg-slate-50 text-slate-600 border-slate-200";
  }
}
