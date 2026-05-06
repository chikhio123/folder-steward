import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getFiles } from "../services/api";
import type { FileRecord } from "../types";
import { formatSize, getFileIcon } from "../utils/format";
import FileDetailPanel from "../components/FileDetailPanel";
import {
  Search,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Database,
  Clock,
  Loader2,
  FolderOpen
} from "lucide-react";
import { twMerge } from "tailwind-merge";

export default function FileListPage() {
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [extension, setExtension] = useState("");
  const [sortBy, setSortBy] = useState("modified_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [selectedFile, setSelectedFile] = useState<FileRecord | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["files", page, keyword, extension, sortBy, sortOrder],
    queryFn: () =>
      getFiles({
        page,
        page_size: 50,
        keyword: keyword || undefined,
        extension: extension || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 50)) : 1;

  const handleOpenFolder = (path: string) => {
    // @ts-ignore
    if (window.electronAPI?.openInFolder) {
      // @ts-ignore
      window.electronAPI.openInFolder(path);
    } else {
      console.warn("Not running in Electron, cannot open folder.");
    }
  };

  return (
    <div className="max-w-6xl mx-auto animation-fade-in flex flex-col h-full">
      <div className="mb-6 shrink-0">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">文件索引库</h2>
        <p className="text-slate-500 mt-1">浏览已建立索引的所有文件记录，支持多维度检索与排序。</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 p-5 mb-6 shadow-sm shrink-0 flex flex-wrap gap-4 items-center">
        <div className="relative flex-1 min-w-[240px]">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-slate-400" />
          </div>
          <input
            type="text"
            value={keyword}
            onChange={(e) => { setKeyword(e.target.value); setPage(1); }}
            placeholder="搜索文件名..."
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400"
          />
        </div>

        <div className="relative w-40">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Filter className="h-4 w-4 text-slate-400" />
          </div>
          <input
            type="text"
            value={extension}
            onChange={(e) => { setExtension(e.target.value); setPage(1); }}
            placeholder="扩展名 (如 .pdf)"
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400"
          />
        </div>

        <div className="h-8 w-px bg-slate-200 hidden sm:block"></div>

        <div className="relative flex items-center">
          <ArrowUpDown className="absolute left-3 w-4 h-4 text-slate-400" />
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            className="pl-9 pr-8 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none cursor-pointer"
          >
            <option value="modified_at">修改时间</option>
            <option value="size_bytes">文件大小</option>
            <option value="filename">文件名称</option>
          </select>
        </div>

        <button
          onClick={() => { setSortOrder((o) => (o === "asc" ? "desc" : "asc")); setPage(1); }}
          className="px-4 py-2.5 border border-slate-200 bg-white rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors flex items-center gap-2 shadow-sm"
        >
          {sortOrder === "asc" ? "↑ 升序" : "↓ 降序"}
        </button>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col bg-white rounded-2xl border border-slate-200/60 shadow-sm relative">
        {/* Table Header */}
        <div className="grid grid-cols-[1fr_minmax(80px,100px)_minmax(100px,120px)_minmax(140px,160px)_100px_40px] gap-4 items-center px-6 py-4 border-b border-slate-100 bg-slate-50/80 sticky top-0 z-10 text-sm font-semibold text-slate-600">
          <div className="pl-2">文件名</div>
          <div>类型</div>
          <div className="text-right">大小</div>
          <div>最后修改</div>
          <div className="text-right">状态</div>
          <div></div>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p>加载文件中...</p>
            </div>
          ) : data?.items?.length ? (
            <div className="divide-y divide-slate-100/60">
              {data.items.map((f: FileRecord) => (
                <div
                  key={f.id}
                  onClick={() => setSelectedFile(f)}
                  className="grid grid-cols-[1fr_minmax(80px,100px)_minmax(100px,120px)_minmax(140px,160px)_100px_40px] gap-4 items-center px-6 py-3.5 hover:bg-slate-50/50 transition-colors group cursor-pointer"
                >
                  <div className="flex flex-col min-w-0 gap-0.5">
                    <div className="flex items-center gap-3 min-w-0">
                      {getFileIcon(f.extension)}
                      <span className="text-sm font-medium text-slate-700 truncate" title={f.filename}>
                        {f.filename}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 truncate pl-8" title={f.current_path}>
                      {f.current_path}
                    </span>
                  </div>
                  <div className="text-sm text-slate-500 truncate">
                    {f.extension ? f.extension.toLowerCase() : "未知"}
                  </div>
                  <div className="text-sm text-slate-600 text-right tabular-nums font-medium">
                    {formatSize(f.size_bytes)}
                  </div>
                  <div className="text-xs text-slate-500 flex items-center gap-1.5 tabular-nums">
                    <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    {f.modified_at ? f.modified_at.slice(0, 16).replace("T", " ") : "-"}
                  </div>
                  <div className="text-right pr-1">
                    <span className={twMerge(
                      "px-2.5 py-1 rounded-lg text-[11px] font-semibold border tracking-wide uppercase",
                      f.status === "active"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200/60"
                        : "bg-slate-50 text-slate-500 border-slate-200"
                    )}>
                      {f.status}
                    </span>
                  </div>
                  <div className="flex justify-end">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenFolder(f.current_path);
                      }}
                      className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                      title="打开所在目录"
                    >
                      <FolderOpen className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20">
              <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                <Database className="w-8 h-8 text-slate-300" />
              </div>
              <p className="font-medium text-slate-500">没有找到匹配的文件</p>
              <p className="text-sm mt-1">您可以尝试更改搜索词或清理筛选器</p>
            </div>
          )}
        </div>

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
            <span className="text-sm text-slate-500 font-medium">
              共 {data?.total ?? 0} 个文件
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
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 font-medium text-sm hover:bg-slate-50 shadow-sm disabled:opacity-40 disabled:hover:bg-white transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Slide-out File Detail Panel */}
      <div
        className={twMerge(
          "fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40 transition-opacity duration-300",
          selectedFile ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={() => setSelectedFile(null)}
      />
      <div
        className={twMerge(
          "fixed inset-y-0 right-0 w-[400px] z-50 transform transition-transform duration-300 ease-in-out",
          selectedFile ? "translate-x-0" : "translate-x-full"
        )}
      >
        <FileDetailPanel file={selectedFile} onClose={() => setSelectedFile(null)} />
      </div>
    </div>
  );
}
