import { useMemo } from "react";
import type { FileSuggestion } from "../types";
import {
  Wand2,
  FolderOpen,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Play,
  FileBox,
  AlertTriangle,
  Filter,
  Loader2,
  Pencil,
  Save,
  X
} from "lucide-react";
import { twMerge } from "tailwind-merge";
import { ConfirmModal } from "../components/ConfirmModal";
import { CustomSelect } from "../components/CustomSelect";
import { Pagination } from "../components/common/Pagination";
import { useSuggestions } from "../hooks/useSuggestions";

export default function SuggestionPage() {
  const { state, actions, mutations } = useSuggestions();
  const { archiveRoot, filter, page, selected, editingId, editPath, showConfirmCancel, data, isLoading } = state;
  const { setArchiveRoot, setFilter, setPage, setSelected, setEditingId, setEditPath, setShowConfirmCancel } = actions;
  const { generateMutation, acceptMutation, rejectOneMutation, savePathMutation, executeMutation, bulkRejectMutation } = mutations;

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
  const pendingItemsOnPage = useMemo(() =>
    data?.items?.filter((s: FileSuggestion) => s.status === "pending" || s.status === "accepted") || [],
    [data?.items]
  );
  const allSelected = useMemo(() =>
    pendingItemsOnPage.length > 0 && selected.size === pendingItemsOnPage.length,
    [pendingItemsOnPage, selected.size]
  );

  const groupedItems = useMemo(() => {
    if (!data?.items) return [];
    const groups: Record<string, FileSuggestion[]> = {};
    data.items.forEach((s: FileSuggestion) => {
      // 提取目标路径所在的目录名
      const dir = s.target_path.replace(/[/\\][^/\\]+$/, "") || "根目录";
      if (!groups[dir]) groups[dir] = [];
      groups[dir].push(s);
    });
    // 转为数组并按目录名排序
    return Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]));
  }, [data?.items]);

  return (
    <div className="max-w-6xl mx-auto animation-fade-in flex flex-col relative min-h-full">
      {/* 柔和的背景光晕效果 */}
      <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="mb-8 shrink-0 relative z-10">
        <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-400 tracking-tight pb-1">整理建议</h2>
        <p className="text-slate-500 mt-1 font-medium">AI 引擎根据文件类型、命名规则自动为您生成的移动分类建议。</p>
      </div>

      <div className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 p-5 mb-6 shadow-sm hover:shadow-md transition-all duration-300 shrink-0 flex flex-col sm:flex-row gap-4 items-center justify-between relative z-10">
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
            className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-2 whitespace-nowrap"
          >
            {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
            生成最新建议
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <div className="h-8 w-px bg-slate-200 hidden sm:block"></div>
          <div className="relative flex items-center w-40">
            <CustomSelect
              value={filter}
              onChange={(value) => { setFilter(value); setPage(1); setSelected(new Set()); }}
              options={[
                { value: "pending", label: "待处理" },
                { value: "accepted", label: "已同意" },
                { value: "rejected", label: "已拒绝" },
                { value: "all", label: "全 部" }
              ]}
              icon={<Filter className="w-4 h-4" />}
              className="w-full"
            />
          </div>

          <button
            onClick={() => setShowConfirmCancel(true)}
            disabled={bulkRejectMutation.isPending || data?.total === 0}
            className="px-4 py-2.5 rounded-xl text-sm font-semibold shadow-sm transition-all flex items-center gap-2 whitespace-nowrap bg-rose-50 text-rose-600 hover:bg-rose-100 hover:shadow-md shadow-rose-600/20 disabled:opacity-50 disabled:pointer-events-none"
          >
            {bulkRejectMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
            取消所有
          </button>
          <button
            onClick={() => executeMutation.mutate()}
            disabled={selected.size === 0 || executeMutation.isPending}
            className={twMerge(
              "px-4 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 whitespace-nowrap",
              selected.size > 0
                ? "bg-gradient-to-r from-blue-600 to-indigo-500 text-white shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5 active:translate-y-0"
                : "bg-slate-100 text-slate-400 pointer-events-none"
            )}
          >
            {executeMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" fill="currentColor" />}
            执行 {selected.size > 0 && `(${selected.size})`}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm relative flex flex-col mb-8">
        {/* Table Header */}
        <div className="grid grid-cols-[auto_1fr_auto] gap-4 items-center px-6 py-4 border-b border-slate-100 bg-slate-50/80 sticky top-0 z-10 text-sm font-semibold text-slate-600 rounded-t-2xl">
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
          <div className="w-40 sm:w-32 text-right pr-2">操作 / 状态</div>
        </div>

        {/* Table Body */}
        <div className="p-4">
          {isLoading ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p>正在加载建议...</p>
            </div>
          ) : data?.items?.length ? (
            <div className="space-y-6">
              {groupedItems.map(([dir, items]) => (
                <div key={dir} className="border border-slate-200/80 rounded-2xl overflow-hidden bg-white shadow-sm">
                  <div className="bg-slate-50/80 px-4 py-3 border-b border-slate-200/80 flex items-center gap-3">
                    <FolderOpen className="w-5 h-5 text-blue-500" />
                    <h4 className="font-semibold text-slate-800 text-sm truncate flex-1">{dir}</h4>
                    <span className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-xs font-bold text-slate-500">
                      {items.length} 项
                    </span>
                  </div>
                  <div className="divide-y divide-slate-100/50">
                    {items.map((s: FileSuggestion) => (
                      <div
                        key={s.id}
                        className={twMerge(
                          "grid grid-cols-[auto_1fr_auto] gap-4 items-center px-4 py-3 transition-all duration-200 group hover:bg-slate-50/50",
                          selected.has(s.id) ? "bg-blue-50/30" : ""
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
                                  {s.target_path.split(/[/\\]/).pop()}
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
                            <span className="text-[11px] px-2 py-0.5 rounded-md font-medium bg-blue-50 text-blue-600 border border-blue-100">
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
                                onClick={() => rejectOneMutation.mutate(s.id)}
                                disabled={rejectOneMutation.isPending}
                                className="p-1.5 text-slate-500 bg-slate-100 hover:bg-rose-100 hover:text-rose-600 rounded-lg transition-colors disabled:opacity-50"
                                title="拒绝建议"
                              >
                                {rejectOneMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
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

              <Pagination 
                currentPage={page} 
                totalPages={totalPages} 
                totalItems={data?.total || 0} 
                onPageChange={(p) => {
                  setPage(p);
                  setSelected(new Set());
                }} 
              />
      </div>

      <ConfirmModal
        isOpen={showConfirmCancel}
        title="取消所有建议"
        message={`确定要取消所有${filter === "all" ? "待处理" : filter}建议吗？此操作不可撤销。`}
        confirmText="确认取消"
        isLoading={bulkRejectMutation.isPending}
        onConfirm={() => {
          bulkRejectMutation.mutate();
        }}
        onCancel={() => setShowConfirmCancel(false)}
      />
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
