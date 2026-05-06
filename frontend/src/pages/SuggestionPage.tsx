import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSuggestions, generateSuggestions, updateSuggestion, executeSuggestions } from "../services/api";
import type { FileSuggestion } from "../types";
import toast from "react-hot-toast";
import {
  Wand2,
  FolderOpen,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Play,
  FileBox,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Filter,
  Loader2,
  Pencil,
  Save,
  X
} from "lucide-react";
import { twMerge } from "tailwind-merge";

export default function SuggestionPage() {
  const queryClient = useQueryClient();
  const [archiveRoot, setArchiveRoot] = useState(() => localStorage.getItem("fs_last_archive_root") || "D:/Archive");
  const [filter, setFilter] = useState("pending");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editPath, setEditPath] = useState("");

  useEffect(() => {
    if (archiveRoot.trim()) {
      localStorage.setItem("fs_last_archive_root", archiveRoot.trim());
    }
  }, [archiveRoot]);

  const { data, isLoading } = useQuery({
    queryKey: ["suggestions", filter, page],
    queryFn: () => getSuggestions({ status: filter === "all" ? undefined : filter, page, page_size: 50 }),
  });

  const generateMutation = useMutation({
    mutationFn: () => generateSuggestions(archiveRoot),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setPage(1);
      setFilter("pending");
      toast.success(`成功生成 ${data.created_count} 条建议`);
    },
    onError: (err) => toast.error(`生成失败: ${err.message}`),
  });

  const acceptMutation = useMutation({
    mutationFn: (id: number) => updateSuggestion(id, { status: "accepted" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      toast.success("已同意该建议");
    },
    onError: (err) => toast.error(`操作失败: ${err.message}`),
  });

  const savePathMutation = useMutation({
    mutationFn: ({ id, path }: { id: number, path: string }) => updateSuggestion(id, { target_path: path }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setEditingId(null);
      toast.success("目标路径已更新");
    },
    onError: (err) => {
      toast.error(`保存失败: ${err.message}`);
    }
  });

  const executeMutation = useMutation({
    mutationFn: () => executeSuggestions(Array.from(selected)),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setSelected(new Set());
      if (data.failed_count > 0) {
        toast.error(`${data.success_count} 个成功，${data.failed_count} 个失败`);
      } else {
        toast.success(`成功执行 ${data.success_count} 条操作`);
      }
    },
    onError: (err) => toast.error(`执行出错: ${err.message}`),
  });

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (!data?.items) return;
    const pendingItems = data.items.filter((s: FileSuggestion) => s.status === "pending" || s.status === "accepted");

    if (selected.size === pendingItems.length && pendingItems.length > 0) {
      setSelected(new Set());
    } else {
      setSelected(new Set(pendingItems.map((s: FileSuggestion) => s.id)));
    }
  };

  const startEdit = (s: FileSuggestion) => {
    setEditingId(s.id);
    setEditPath(s.target_path);
  };

  const saveEdit = (id: number) => {
    if (editPath.trim()) {
      savePathMutation.mutate({ id, path: editPath.trim() });
    }
  };

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 50)) : 1;
  const pendingItemsOnPage = data?.items?.filter((s: FileSuggestion) => s.status === "pending" || s.status === "accepted") || [];
  const allSelected = pendingItemsOnPage.length > 0 && selected.size === pendingItemsOnPage.length;

  return (
    <div className="max-w-6xl mx-auto animation-fade-in flex flex-col h-full">
      <div className="mb-6 shrink-0">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">整理建议</h2>
        <p className="text-slate-500 mt-1">AI 引擎根据文件类型、命名规则自动为您生成的移动分类建议。</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 p-5 mb-6 shadow-sm shrink-0 flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="flex-1 w-full flex items-center gap-3">
          <div className="relative flex-1 max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FolderOpen className="h-4 w-4 text-slate-400" />
            </div>
            <input
              type="text"
              value={archiveRoot}
              onChange={(e) => setArchiveRoot(e.target.value)}
              placeholder="归档根目录，如 D:/Archive"
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400"
            />
          </div>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold shadow-sm shadow-blue-600/20 hover:bg-blue-700 hover:shadow-md active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-2 whitespace-nowrap"
          >
            {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
            生成最新建议
          </button>
        </div>

        <div className="flex items-center gap-4 w-full sm:w-auto">
          <div className="h-8 w-px bg-slate-200 hidden sm:block"></div>
          <div className="relative flex items-center">
            <Filter className="absolute left-3 w-4 h-4 text-slate-400" />
            <select
              value={filter}
              onChange={(e) => { setFilter(e.target.value); setPage(1); setSelected(new Set()); }}
              className="pl-9 pr-8 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none cursor-pointer"
            >
              <option value="pending">待处理</option>
              <option value="accepted">已同意</option>
              <option value="rejected">已拒绝</option>
              <option value="all">全 部</option>
            </select>
          </div>

          <button
            onClick={() => executeMutation.mutate()}
            disabled={selected.size === 0 || executeMutation.isPending}
            className={twMerge(
              "px-5 py-2.5 rounded-xl text-sm font-semibold shadow-sm transition-all flex items-center gap-2 whitespace-nowrap",
              selected.size > 0
                ? "bg-emerald-600 text-white hover:bg-emerald-700 hover:shadow-md shadow-emerald-600/20"
                : "bg-slate-100 text-slate-400 pointer-events-none"
            )}
          >
            {executeMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" fill="currentColor" />}
            执行选中项 {selected.size > 0 && `(${selected.size})`}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col bg-white rounded-2xl border border-slate-200/60 shadow-sm relative">
        {/* Table Header */}
        <div className="grid grid-cols-[auto_1fr_auto] gap-4 items-center px-6 py-4 border-b border-slate-100 bg-slate-50/80 sticky top-0 z-10 text-sm font-semibold text-slate-600">
          <div className="w-6 flex justify-center">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={toggleAll}
              disabled={pendingItemsOnPage.length === 0}
              className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/50 disabled:opacity-50"
            />
          </div>
          <div className="pl-2">整理详情</div>
          <div className="w-40 text-right pr-2">操作 / 状态</div>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p>正在加载建议...</p>
            </div>
          ) : data?.items?.length ? (
            <div className="space-y-1.5">
              {data.items.map((s: FileSuggestion) => (
                <div
                  key={s.id}
                  className={twMerge(
                    "grid grid-cols-[auto_1fr_auto] gap-4 items-center px-4 py-3 rounded-xl transition-all duration-200 group",
                    selected.has(s.id)
                      ? "bg-blue-50/50 ring-1 ring-blue-200 shadow-sm"
                      : "hover:bg-slate-50 border border-transparent hover:border-slate-100"
                  )}
                >
                  <div className="w-6 flex justify-center mt-1 self-start">
                    <input
                      type="checkbox"
                      checked={selected.has(s.id)}
                      onChange={() => toggle(s.id)}
                      disabled={s.status !== "pending" && s.status !== "accepted"}
                      className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/50 disabled:opacity-50 cursor-pointer"
                    />
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <FileBox className="w-4 h-4 text-slate-400 shrink-0" />
                      <span className="text-sm font-medium text-slate-700 truncate" title={s.source_path}>
                        {s.source_path.split(/[/\\]/).pop()}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 ml-1 mb-2 text-xs">
                      <div className="text-slate-400 max-w-[40%] truncate" title={s.source_path}>
                        {s.source_path}
                      </div>
                      <ArrowRight className="w-3.5 h-3.5 text-blue-500 shrink-0" />

                      {editingId === s.id ? (
                        <div className="flex items-center gap-1 flex-1">
                          <input
                            type="text"
                            value={editPath}
                            onChange={(e) => setEditPath(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') saveEdit(s.id);
                              if (e.key === 'Escape') setEditingId(null);
                            }}
                            className="flex-1 bg-white border border-blue-300 text-slate-800 rounded px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/50 shadow-inner"
                            autoFocus
                          />
                          <button onClick={() => saveEdit(s.id)} className="p-1 text-emerald-600 hover:bg-emerald-50 rounded">
                            <Save className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => setEditingId(null)} className="p-1 text-slate-400 hover:bg-slate-100 rounded">
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 flex-1 min-w-0">
                          <div className="text-blue-600 font-medium truncate" title={s.target_path}>
                            {s.target_path}
                          </div>
                          {s.status === "pending" && (
                            <button
                              onClick={() => startEdit(s)}
                              className="p-1 text-slate-400 opacity-0 group-hover:opacity-100 hover:text-blue-600 hover:bg-blue-50 rounded transition-all shrink-0"
                              title="修改目标路径"
                            >
                              <Pencil className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2 items-center">
                      <span className="text-[11px] px-2 py-0.5 rounded-md font-medium bg-slate-100 text-slate-600">
                        {s.reason || "系统默认策略"}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded-md font-medium bg-indigo-50 text-indigo-600 border border-indigo-100">
                        置信度 {(s.confidence * 100).toFixed(0)}%
                      </span>
                      {s.conflict_status !== "none" && (
                        <span className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md font-medium bg-amber-50 text-amber-700 border border-amber-200">
                          <AlertTriangle className="w-3 h-3" />
                          目标已存在
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-start mt-1">
                    {s.status === "pending" ? (
                      <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => acceptMutation.mutate(s.id)}
                          className="p-1.5 text-emerald-600 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-colors tooltip-trigger"
                          title="同意建议"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            updateSuggestion(s.id, { status: "rejected" })
                              .then(() => {
                                queryClient.invalidateQueries({ queryKey: ["suggestions"] });
                                toast.success("已拒绝该建议");
                              })
                              .catch((err) => toast.error(`拒绝失败: ${err.message}`));
                          }}
                          className="p-1.5 text-slate-500 bg-slate-100 hover:bg-rose-100 hover:text-rose-600 rounded-lg transition-colors"
                          title="拒绝建议"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <span className={twMerge("px-2.5 py-1 text-xs font-semibold rounded-lg border", statusBadgeStyle(s.status))}>
                        {statusText(s.status)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400">
              <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                <Wand2 className="w-8 h-8 text-slate-300" />
              </div>
              <p className="font-medium text-slate-500">没有符合条件的整理建议</p>
              <p className="text-sm mt-1">您可以尝试重新生成或调整右上角的过滤器</p>
            </div>
          )}
        </div>

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
            <span className="text-sm text-slate-500">
              第 <strong className="text-slate-700">{page}</strong> 页，共 {totalPages} 页
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => { setPage((p) => p - 1); setSelected(new Set()); }}
                className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => { setPage((p) => p + 1); setSelected(new Set()); }}
                className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function statusText(status: string): string {
  switch (status) {
    case "pending": return "待处理";
    case "accepted": return "已同意";
    case "rejected": return "已拒绝";
    case "executed": return "已执行";
    case "failed": return "执行失败";
    case "superseded": return "已过期";
    default: return status;
  }
}

function statusBadgeStyle(status: string): string {
  switch (status) {
    case "pending": return "bg-amber-50 text-amber-700 border-amber-200/50";
    case "accepted": return "bg-blue-50 text-blue-700 border-blue-200/50";
    case "rejected": return "bg-slate-100 text-slate-500 border-slate-200";
    case "executed": return "bg-emerald-50 text-emerald-700 border-emerald-200/50";
    case "failed": return "bg-rose-50 text-rose-700 border-rose-200/50";
    case "superseded": return "bg-slate-50 text-slate-400 border-slate-200 border-dashed";
    default: return "bg-slate-50 text-slate-500 border-slate-200";
  }
}
