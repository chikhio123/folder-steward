import { formatSize, getFileIcon } from "../utils/format";
import FileDetailPanel from "../components/FileDetailPanel";
import { Pagination } from '../components/common/Pagination';
import { useFileList } from '../hooks/useFileList';
import type { FileRecord } from "../types";
import {
  Search,
  Filter,
  ArrowUpDown,
  Database,
  Clock,
  Loader2,
  FolderOpen,
  ChevronUp,
  ChevronDown
} from "lucide-react";
import { twMerge } from "tailwind-merge";
import { CustomSelect } from "../components/CustomSelect";

const SortIcon = ({ active, order }: { active: boolean, order: "asc" | "desc" }) => (
  <div className={twMerge(
    "flex flex-col -space-y-1 transition-all duration-200 group-hover:scale-125",
    active ? "opacity-100" : "opacity-0 group-hover:opacity-100"
  )}>
    <ChevronUp className={twMerge("w-3 h-3", active && order === "asc" ? "text-blue-600" : "text-slate-400")} strokeWidth={active && order === "asc" ? 3 : 2} />
    <ChevronDown className={twMerge("w-3 h-3", active && order === "desc" ? "text-blue-600" : "text-slate-400")} strokeWidth={active && order === "desc" ? 3 : 2} />
  </div>
);

export default function FileListPage() {
  const { state, actions, query } = useFileList();
  const { page, keyword, extension, sortBy, sortOrder, selectedFile } = state;
  const { setPage, setKeyword, setExtension, setSortBy, setSortOrder, setSelectedFile } = actions;
  const { data, isLoading } = query;

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 50)) : 1;

  const handleOpenFolder = (path: string) => {
    // @ts-ignore
    if (window.electronAPI?.openInFolder) {
      window.electronAPI.openInFolder(path);
    } else {
      console.warn("Not running in Electron, cannot open folder.");
    }
  };

  return (
    <div className="max-w-6xl mx-auto animation-fade-in flex flex-col relative min-h-full">
      {/* 背景光晕 */}
      <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="mb-6 shrink-0 z-20 bg-slate-50/80 backdrop-blur-xl border-b border-slate-200/50 pb-4 pt-2 -mx-4 px-4 sm:-mx-0 sm:px-0">
        <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-400 tracking-tight pb-1">文件索引库</h2>
        <p className="text-slate-500 mt-1 font-medium">浏览已建立索引的所有文件记录，支持多维度检索与排序。</p>
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

        <div className="relative flex items-center w-40">
          <CustomSelect
            value={sortBy}
            onChange={(value) => { setSortBy(value); setPage(1); }}
            options={[
              { value: "modified_at", label: "修改时间" },
              { value: "size_bytes", label: "文件大小" },
              { value: "filename", label: "文件名称" }
            ]}
            icon={<ArrowUpDown className="w-4 h-4" />}
            className="w-full"
          />
        </div>

        <button
          onClick={() => { setSortOrder((o) => (o === "asc" ? "desc" : "asc")); setPage(1); }}
          className="px-4 py-2.5 border border-slate-200 bg-white rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors flex items-center gap-2 shadow-sm"
        >
          {sortOrder === "asc" ? "↑ 升序" : "↓ 降序"}
        </button>
      </div>

      <div className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 shadow-sm relative flex flex-col mb-8">
        {/* Table Header */}
        <div className="grid grid-cols-[1fr_minmax(80px,100px)_minmax(100px,120px)_minmax(140px,160px)_100px_40px] gap-4 items-center px-6 py-4 border-b border-slate-100/80 bg-slate-50/40 sticky top-0 z-10 text-sm font-semibold text-slate-600 rounded-t-2xl">
          <div className="pl-2">
            <button
              onClick={() => {
                if (sortBy === "filename") setSortOrder(o => o === "asc" ? "desc" : "asc");
                else { setSortBy("filename"); setSortOrder("asc"); }
                setPage(1);
              }}
              className="flex items-center gap-1.5 hover:text-blue-600 transition-colors group"
            >
              文件名
              <SortIcon active={sortBy === "filename"} order={sortOrder} />
            </button>
          </div>
          <div>类型</div>
          <div className="flex justify-center">
            <button
              onClick={() => {
                if (sortBy === "size_bytes") setSortOrder(o => o === "asc" ? "desc" : "asc");
                else { setSortBy("size_bytes"); setSortOrder("desc"); }
                setPage(1);
              }}
              className="flex items-center gap-1.5 hover:text-blue-600 transition-colors group"
            >
              大小
              <SortIcon active={sortBy === "size_bytes"} order={sortOrder} />
            </button>
          </div>
          <div className="flex justify-start">
            <button
              onClick={() => {
                if (sortBy === "modified_at") setSortOrder(o => o === "asc" ? "desc" : "asc");
                else { setSortBy("modified_at"); setSortOrder("desc"); }
                setPage(1);
              }}
              className="flex items-center gap-1.5 hover:text-blue-600 transition-colors group"
            >
              最后修改
              <SortIcon active={sortBy === "modified_at"} order={sortOrder} />
            </button>
          </div>
          <div className="text-center">状态</div>
          <div></div>
        </div>

        {/* Table Body */}
        <div className="p-2">
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
                  <div className="text-sm text-slate-600 text-center tabular-nums font-medium">
                    {formatSize(f.size_bytes)}
                  </div>
                  <div className="text-xs text-slate-500 flex items-center gap-1.5 tabular-nums">
                    <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    {f.modified_at ? f.modified_at.slice(0, 16).replace("T", " ") : "-"}
                  </div>
                  <div className="flex justify-center">
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
        <Pagination currentPage={page} totalPages={totalPages} totalItems={data?.total || 0} onPageChange={setPage} />
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
        {selectedFile && <FileDetailPanel file={selectedFile} onClose={() => setSelectedFile(null)} />}
      </div>
    </div>
  );
}
