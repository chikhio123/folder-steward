import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getDuplicates, createDuplicateSuggestions } from "../services/api";
import { CopyX, FileBox, Database, Loader2, Fingerprint, CheckCircle2 } from "lucide-react";
import { twMerge } from "tailwind-merge";
import toast from "react-hot-toast";
import { formatSize } from "../utils/format";

export default function DuplicatePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["duplicates"],
    queryFn: getDuplicates,
  });

  const [processingKey, setProcessingKey] = useState<string | null>(null);

  const suggestMutation = useMutation({
    mutationFn: ({ sha256, filename, keepFileId }: { sha256: string; filename: string; keepFileId: number }) =>
      createDuplicateSuggestions(sha256, filename, keepFileId),
    onMutate: (variables) => {
      setProcessingKey(variables.sha256 + variables.filename);
    },
    onSuccess: (data) => {
      toast.success(`成功生成 ${data.created_count} 条建议！`);
    },
    onError: (err) => {
      toast.error(`生成建议失败: ${err.message}`);
    },
    onSettled: () => {
      setProcessingKey(null);
    }
  });

  return (
    <div className="max-w-4xl mx-auto animation-fade-in flex flex-col h-full relative">
      <div className="mb-6 shrink-0 sticky top-0 z-20 bg-white/60 backdrop-blur-xl border-b border-slate-200/50 pb-4 pt-2 -mx-4 px-4 sm:-mx-0 sm:px-0">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">重复文件清理</h2>
        <p className="text-slate-500 mt-1">基于 SHA-256 哈希值精确查找出的完全相同的文件副本。点击右侧“保留此副本”即可生成其他副本的整理建议。</p>
      </div>

      <div className="flex-1 overflow-y-auto pb-8">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center text-slate-400 py-20 space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <p>正在比对文件指纹...</p>
          </div>
        ) : data?.groups?.length ? (
          <div className="space-y-5">
            {data.groups.map((group, i) => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden group hover:border-slate-300 transition-colors">
                <div className="bg-slate-50/80 border-b border-slate-100 px-5 py-3.5 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1.5 text-sm font-semibold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200/50">
                      <CopyX className="w-4 h-4" />
                      {group.count} 个副本
                    </span>
                    <span className="flex items-center gap-1.5 text-sm font-medium text-slate-600">
                      <Database className="w-4 h-4 text-slate-400" />
                      单文件大小: {formatSize(group.size_bytes)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-white px-2 py-1 rounded-md border border-slate-200 shadow-sm" title={group.sha256}>
                    <Fingerprint className="w-3.5 h-3.5 text-blue-400" />
                    {group.sha256.slice(0, 16)}...
                  </div>
                </div>

                <div className="p-2 space-y-1">
                  {group.files.map((f) => (
                    <div key={f.id} className="flex items-center justify-between gap-3 text-sm text-slate-700 hover:bg-slate-50 rounded-xl px-4 py-2.5 transition-colors">
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
                        onClick={() => suggestMutation.mutate({ sha256: group.sha256, filename: group.files[0].filename, keepFileId: f.id })}
                        disabled={suggestMutation.isPending && processingKey === (group.sha256 + group.files[0].filename)}
                        className={twMerge(
                          "shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5 border",
                          suggestMutation.isPending && processingKey === (group.sha256 + group.files[0].filename)
                            ? "bg-slate-100 text-slate-400 border-slate-200"
                            : "bg-white text-indigo-600 border-indigo-200 hover:bg-indigo-50 hover:border-indigo-300"
                        )}
                      >
                        {suggestMutation.isPending && processingKey === (group.sha256 + group.files[0].filename) ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        )}
                        保留此副本
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20 bg-white rounded-2xl border border-slate-200/60 border-dashed">
            <div className="w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mb-4">
              <CopyX className="w-8 h-8 text-emerald-400" />
            </div>
            <p className="font-medium text-slate-500">太棒了！没有发现重复文件</p>
            <p className="text-sm mt-1">您的磁盘空间利用率非常完美</p>
          </div>
        )}
      </div>
    </div>
  );
}
