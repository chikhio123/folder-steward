import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDuplicates, isolateDuplicates } from "../../../services/api";
import { CopyX, FileBox, Database, Loader2, Fingerprint, CheckCircle2, ChevronDown, ChevronRight, Wand2 } from "lucide-react";
import { twMerge } from "tailwind-merge";
import toast from "react-hot-toast";
import { formatSize } from "../../../utils/format";
import { ConfirmModal } from "../../../components/ui/ConfirmModal";

export function DuplicateIsolationPanel() {
  const queryClient = useQueryClient();
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAutoConfirm, setShowAutoConfirm] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["duplicates"],
    queryFn: getDuplicates,
  });

  const [processingKey, setProcessingKey] = useState<string | null>(null);

  const isolateMutation = useMutation({
    mutationFn: ({ sha256, filename, keepFileId }: { sha256: string; filename: string; keepFileId: number }) =>
      isolateDuplicates("manual", [{ sha256, filename, keep_file_id: keepFileId }]),
    onMutate: (variables) => {
      setProcessingKey(variables.sha256);
    },
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["duplicates"] });
      queryClient.invalidateQueries({ queryKey: ["operations"] });
      if (res.skipped && res.skipped.length > 0) {
        toast.success(`成功隔离 ${res.success_count} 项。已跳过 ${res.skipped.length} 项（被其他 AI 计划占用）。`);
      } else {
        toast.success(`成功隔离 ${res.success_count} 个重复副本！`);
      }
    },
    onError: (err: any) => {
      toast.error(`隔离失败: ${err.message}`);
    },
    onSettled: () => {
      setProcessingKey(null);
    }
  });

  const autoIsolateMutation = useMutation({
    mutationFn: () => isolateDuplicates("auto"),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["duplicates"] });
      queryClient.invalidateQueries({ queryKey: ["operations"] });
      toast.success(`智能隔离完成！成功 ${res.success_count} 项，失败 ${res.failed_count} 项。`);
      setIsExpanded(false);
    },
    onError: (err: any) => {
      toast.error(`一键隔离失败: ${err.message}`);
    }
  });

  const groupCount = data?.groups?.length || 0;

  if (isLoading || groupCount === 0) return null;

  return (
    <div className="mb-8">
      {/* Banner */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full bg-gradient-to-r from-blue-50/50 to-indigo-50/30 border border-blue-200/50 rounded-2xl p-4 flex items-center justify-between shadow-sm hover:shadow-md transition-all duration-300 group"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100/80 rounded-xl text-blue-600">
            <CopyX className="w-5 h-5" />
          </div>
          <div className="text-left">
            <h3 className="text-sm font-bold text-blue-800">
              检测到 {groupCount} 组完全重复文件
            </h3>
            <p className="text-xs text-blue-600/80 mt-0.5 font-medium">
              建议在处理 AI 分类前先行隔离，可大幅减少大模型分析负担与 Token 消耗。
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-blue-600 font-semibold text-sm">
          {isExpanded ? "收起面板" : "展开处理"}
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </div>
      </button>

      {/* Accordion Content */}
      {isExpanded && (
        <div className="mt-4 bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden animation-fade-in flex flex-col max-h-[600px]">
          <div className="px-6 py-4 border-b border-slate-100/80 bg-slate-50/40 flex items-center justify-between sticky top-0 z-10">
            <div>
              <h3 className="text-sm font-bold text-slate-800">重复文件物理隔离区</h3>
              <p className="text-xs text-slate-500 mt-0.5">直接将多余副本移入 Trash_Duplicates，绕过 AI 建议流，支持在操作历史中回滚。</p>
            </div>
            <button
              onClick={() => setShowAutoConfirm(true)}
              disabled={autoIsolateMutation.isPending}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-md shadow-blue-500/20 hover:shadow-lg hover:-translate-y-0.5 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {autoIsolateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
              一键智能隔离
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {data?.groups.map((group: any, i: number) => (
              <div key={i} className="bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-hidden group hover:shadow-md transition-all duration-300">
                <div className="bg-slate-50/40 border-b border-slate-100/80 px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200/50">
                      <CopyX className="w-3.5 h-3.5" />
                      {group.count} 个副本
                    </span>
                    <span className="flex items-center gap-1.5 text-xs font-medium text-slate-600">
                      <Database className="w-3.5 h-3.5 text-slate-400" />
                      {formatSize(group.size_bytes)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 bg-white px-2 py-1 rounded border border-slate-200 shadow-sm truncate max-w-[200px]" title={group.sha256}>
                    <Fingerprint className="w-3 h-3 text-blue-400 shrink-0" />
                    <span className="truncate">{group.sha256.slice(0, 16)}...</span>
                  </div>
                </div>

                <div className="p-2 space-y-1">
                  {group.files.map((f: any) => (
                    <div key={f.id} className="flex items-center justify-between gap-3 text-sm text-slate-700 hover:bg-slate-50 rounded-lg px-3 py-2 transition-colors">
                      <div className="flex items-start gap-3 min-w-0 flex-1">
                        <FileBox className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                        <div className="min-w-0 flex-1">
                          <div className="font-medium text-slate-800 truncate mb-0.5" title={f.filename}>
                            {f.filename}
                          </div>
                          <div className="text-xs text-slate-500 truncate" title={f.current_path}>
                            {f.current_path}
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => isolateMutation.mutate({ sha256: group.sha256, filename: group.filename, keepFileId: f.id })}
                        disabled={isolateMutation.isPending && processingKey === group.sha256}
                        className={twMerge(
                          "shrink-0 px-3 py-1.5 rounded-md text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5",
                          isolateMutation.isPending && processingKey === group.sha256
                            ? "bg-slate-100 text-slate-400 border border-slate-200"
                            : "bg-white text-emerald-600 border border-emerald-200 hover:bg-emerald-50 hover:border-emerald-300"
                        )}
                      >
                        {isolateMutation.isPending && processingKey === group.sha256 ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        )}
                        保留此份 (隔离其余)
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <ConfirmModal
        isOpen={showAutoConfirm}
        title="一键智能隔离"
        message="确定要让系统智能挑选并隔离所有重复文件吗？将优先保留处于归档目录内、路径最短和最早创建的副本。"
        confirmText="确认隔离"
        confirmVariant="primary"
        isLoading={autoIsolateMutation.isPending}
        onConfirm={() => {
          setShowAutoConfirm(false);
          autoIsolateMutation.mutate();
        }}
        onCancel={() => setShowAutoConfirm(false)}
      />
    </div>
  );
}
