import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getFileContent, forceExtractFile } from "../services/api";
import { formatSize, getFileIcon } from "../utils/format";
import type { FileRecord } from "../types";
import { X, FileText, Loader2, RefreshCw, AlertCircle, CheckCircle2 } from "lucide-react";
import { twMerge } from "tailwind-merge";
import toast from "react-hot-toast";

interface FileDetailPanelProps {
  file: FileRecord | null;
  onClose: () => void;
}

export default function FileDetailPanel({ file, onClose }: FileDetailPanelProps) {
  const queryClient = useQueryClient();

  const { data: contentData, isLoading } = useQuery({
    queryKey: ["file-content", file?.id],
    queryFn: () => getFileContent(file!.id),
    enabled: !!file,
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data?.extract_status;
      return (status === "pending" || status === "running") ? 1000 : false;
    }
  });

  const extractMutation = useMutation({
    mutationFn: () => forceExtractFile(file!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["file-content", file!.id] });
      toast.success("提取任务已提交后台");
    },
    onError: (err) => {
      toast.error(`提取失败: ${err.message}`);
    }
  });

  if (!file) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl border-l border-slate-200 flex flex-col z-50 transform transition-transform duration-300">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
        <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          {getFileIcon(file.extension)}
          文件详情
        </h3>
        <button
          onClick={onClose}
          className="p-1.5 text-slate-400 hover:bg-slate-200 hover:text-slate-700 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Metadata */}
        <div className="mb-8">
          <div className="text-lg font-bold text-slate-800 break-words leading-tight mb-4">
            {file.filename}
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex">
              <span className="w-20 text-slate-400 shrink-0">当前路径</span>
              <span className="text-slate-700 break-all">{file.current_path}</span>
            </div>
            <div className="flex">
              <span className="w-20 text-slate-400 shrink-0">文件大小</span>
              <span className="text-slate-700 tabular-nums">{formatSize(file.size_bytes)}</span>
            </div>
            <div className="flex">
              <span className="w-20 text-slate-400 shrink-0">修改时间</span>
              <span className="text-slate-700 tabular-nums">{file.modified_at?.replace("T", " ")}</span>
            </div>
            <div className="flex">
              <span className="w-20 text-slate-400 shrink-0">数字指纹</span>
              <span className="text-slate-700 font-mono text-xs break-all bg-slate-50 p-1.5 rounded border border-slate-100">
                {file.sha256 || "未计算"}
              </span>
            </div>
          </div>
        </div>

        {/* Content Extraction Status & Preview */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-slate-800 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-500" />
              正文提取预览
            </h4>
            {(!contentData || contentData.extract_status !== "running") && (
              <button
                onClick={() => extractMutation.mutate()}
                disabled={extractMutation.isPending}
                className="flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 px-2 py-1 rounded transition-colors disabled:opacity-50"
              >
                {extractMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                重新提取
              </button>
            )}
          </div>

          {isLoading && !contentData ? (
            <div className="py-8 flex flex-col items-center justify-center text-slate-400 space-y-2 border border-slate-100 rounded-xl bg-slate-50/50">
              <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
              <span className="text-sm">正在加载提取状态...</span>
            </div>
          ) : contentData ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm p-3 rounded-xl border border-slate-100 bg-slate-50">
                <span className="text-slate-500">提取状态</span>
                <span className={twMerge("px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider", statusBadgeStyle(contentData.extract_status))}>
                  {statusIcon(contentData.extract_status)}
                  <span className="ml-1">{statusText(contentData.extract_status)}</span>
                </span>
              </div>

              {contentData.extract_status === "completed" && (
                <div className="text-sm text-slate-500 mb-2">
                  成功提取了 <strong className="text-slate-700">{contentData.text_length}</strong> 个字符。
                </div>
              )}

              {contentData.preview ? (
                <div className="relative">
                  <div className="text-xs text-slate-600 leading-relaxed font-mono whitespace-pre-wrap break-words bg-slate-50 border border-slate-200 rounded-xl p-4 max-h-[300px] overflow-y-auto custom-scrollbar">
                    {contentData.preview}
                  </div>
                  {contentData.text_length > 5000 && (
                    <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-slate-50 to-transparent pointer-events-none rounded-b-xl flex items-end justify-center pb-2">
                      <span className="text-[10px] text-slate-400 font-medium">预览已截断</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-8 text-center text-sm text-slate-400 bg-slate-50 border border-slate-100 rounded-xl border-dashed">
                  {contentData.extract_status === "failed" ? "提取失败，无内容可预览" : "暂无正文内容"}
                </div>
              )}
            </div>
          ) : (
            <div className="py-8 flex flex-col items-center justify-center text-slate-400 space-y-2 border border-slate-200 border-dashed rounded-xl bg-slate-50/50">
              <FileText className="w-8 h-8 text-slate-300" />
              <span className="text-sm font-medium">该文件尚未进行提取尝试</span>
              <button
                onClick={() => extractMutation.mutate()}
                className="mt-2 text-xs bg-white border border-slate-200 shadow-sm text-slate-600 px-3 py-1.5 rounded-lg hover:bg-slate-50 transition-colors"
              >
                立即提取
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function statusText(status: string): string {
  switch (status) {
    case "completed": return "已完成";
    case "failed": return "失败";
    case "pending": return "排队中";
    case "running": return "提取中";
    case "skipped": return "跳过";
    case "stale": return "已过期";
    default: return status;
  }
}

function statusBadgeStyle(status: string): string {
  switch (status) {
    case "completed": return "bg-emerald-100 text-emerald-700 border-emerald-200";
    case "failed": return "bg-rose-100 text-rose-700 border-rose-200";
    case "running":
    case "pending": return "bg-blue-100 text-blue-700 border-blue-200";
    case "skipped":
    case "stale": return "bg-slate-100 text-slate-500 border-slate-200";
    default: return "bg-slate-100 text-slate-600 border-slate-200";
  }
}

function statusIcon(status: string) {
  switch (status) {
    case "completed": return <CheckCircle2 className="inline w-3 h-3" />;
    case "failed": return <AlertCircle className="inline w-3 h-3" />;
    case "running":
    case "pending": return <Loader2 className="inline w-3 h-3 animate-spin" />;
    default: return null;
  }
}