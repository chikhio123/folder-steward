import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDuplicates, isolateDuplicates } from "../services/api";
import { CopyX, FileBox, Database, Loader2, Fingerprint, CheckCircle2 } from "lucide-react";
import { twMerge } from "tailwind-merge";
import toast from "react-hot-toast";
import { formatSize } from "../utils/format";

export default function DuplicatePage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["duplicates"],
    queryFn: getDuplicates,
  });

  const [processingKey, setProcessingKey] = useState<string | null>(null);

  const isolateMutation = useMutation({
    mutationFn: ({ sha256, keepFileId }: { sha256: string; keepFileId: number }) =>
      isolateDuplicates("manual", [{ sha256, keep_file_id: keepFileId }]),
    onMutate: (variables) => {
      setProcessingKey(variables.sha256);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["duplicates"] });
      toast.success(`成功隔离 ${data.success_count} 个重复副本！`);
    },
    onError: (err) => {
      toast.error(`隔离失败: ${err.message}`);
    },
    onSettled: () => {
      setProcessingKey(null);
    }
  });

  return (
    <div className="max-w-4xl mx-auto animation-fade-in flex flex-col relative min-h-full">
      {/* 背景光晕 */}
      <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-amber-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="mb-6 shrink-0 z-20 pb-4 pt-2 -mx-4 px-4 sm:-mx-0 sm:px-0">
        <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-amber-600 to-orange-400 tracking-tight pb-1">重复文件清理</h2>
        <p className="text-slate-500 mt-1 font-medium">基于 SHA-256 哈希值精确查找出的完全相同的文件副本。点击右侧“保留此副本”即可生成其他副本的整理建议。</p>
      </div>

      <div className="pb-8">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center text-slate-400 py-20 space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <p>正在比对文件指纹...</p>
          </div>
        ) : data?.groups?.length ? (
          <div className="space-y-5">
            {data.groups.map((group, i) => (
              <div key={i} className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden group hover:shadow-md hover:-translate-y-0.5 transition-all duration-300">
                <div className="bg-slate-50/40 backdrop-blur-sm border-b border-slate-100/80 px-5 py-3.5 flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="flex items-center gap-1.5 text-sm font-semibold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200/50">
                      <CopyX className="w-4 h-4" />
                      {group.count} 个副本
                    </span>
                    <span className="flex items-center gap-1.5 text-sm font-medium text-slate-600">
                      <Database className="w-4 h-4 text-slate-400" />
                      {formatSize(group.size_bytes)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-white px-2 py-1 rounded-md border border-slate-200 shadow-sm truncate max-w-full" title={group.sha256}>
                    <Fingerprint className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span className="truncate">{group.sha256.slice(0, 16)}...</span>
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
                        onClick={() => isolateMutation.mutate({ sha256: group.sha256, keepFileId: f.id })}
                        disabled={isolateMutation.isPending && processingKey === group.sha256}
                        className={twMerge(
                          "shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5",
                          isolateMutation.isPending && processingKey === group.sha256
                            ? "bg-slate-100 text-slate-400 border border-slate-200"
                            : "bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-600 border border-emerald-200 hover:from-emerald-100 hover:to-teal-100 hover:border-emerald-300 hover:shadow-md hover:-translate-y-0.5"
                        )}
                      >
                        {isolateMutation.isPending && processingKey === group.sha256 ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        )}
                        保留此副本 (隔离其余)
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
