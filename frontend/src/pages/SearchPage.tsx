import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchFiles } from "../services/api";
import { getFileIcon } from "../utils/format";
import {
  Search as SearchIcon,
  Filter,
  FileBox,
  FolderOpen,
  ChevronLeft,
  ChevronRight,
  Database,
  Loader2
} from "lucide-react";
import { twMerge } from "tailwind-merge";
import { CustomSelect } from "../components/CustomSelect";

export default function SearchPage() {
  const [queryInput, setQueryInput] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [scope, setScope] = useState("all");
  const [page, setPage] = useState(1);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(queryInput);
      setPage(1);
    }, 500);
    return () => clearTimeout(timer);
  }, [queryInput]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["search", debouncedQuery, scope, page],
    queryFn: () =>
      searchFiles({
        q: debouncedQuery,
        scope,
        page,
        page_size: 50,
      }),
    enabled: debouncedQuery.trim().length > 0,
    staleTime: 60000,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 50)) : 1;

  const handleOpenFolder = (path: string) => {
    if (window.electronAPI?.openInFolder) {
      window.electronAPI.openInFolder(path);
    }
  };

  return (
    <div className="max-w-5xl mx-auto animation-fade-in flex flex-col h-full">
      <div className="mb-6 shrink-0">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">全局搜索</h2>
        <p className="text-slate-500 mt-1">在文件名称和已提取的纯文本内容中进行极速匹配与搜索。</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 p-5 mb-6 shadow-sm shrink-0 flex flex-wrap gap-4 items-center">
        <div className="relative flex-1 min-w-[240px]">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <SearchIcon className="h-5 w-5 text-blue-500" />
          </div>
          <input
            type="text"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="输入搜索关键词..."
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl pl-11 pr-4 py-3 text-base font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400 shadow-inner"
            autoFocus
          />
        </div>

        <div className="relative flex items-center w-48">
          <CustomSelect
            value={scope}
            onChange={(value) => setScope(value)}
            options={[
              { value: "all", label: "全文 + 文件名" },
              { value: "filename", label: "仅搜索文件名" },
              { value: "content", label: "仅搜索正文" }
            ]}
            icon={<Filter className="w-4 h-4" />}
            className="w-full"
          />
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col bg-white rounded-2xl border border-slate-200/60 shadow-sm relative">
        {/* Results Area */}
        <div className="flex-1 overflow-y-auto">
          {!debouncedQuery.trim() ? (
             <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20">
               <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mb-4">
                 <SearchIcon className="w-8 h-8 text-blue-300" />
               </div>
               <p className="font-medium text-slate-500">输入关键字开始搜索</p>
               <p className="text-sm mt-1">支持纯文本、Markdown、PDF 和 Word 内容的检索</p>
             </div>
          ) : isLoading ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p>正在全文检索中...</p>
            </div>
          ) : isError ? (
            <div className="h-full flex flex-col items-center justify-center text-rose-500 py-20">
              <p className="font-medium">搜索出现错误，请确保关键词合法。</p>
            </div>
          ) : data?.items?.length ? (
            <div className="divide-y divide-slate-100/60 p-2">
              {data.items.map((item: import("../types").SearchResultItem) => (
                <div key={item.file_id} className="p-4 hover:bg-slate-50/80 transition-colors rounded-xl group relative">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <div className="mt-1">
                         {getFileIcon(item.extension)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-base font-semibold text-slate-800 truncate" title={item.filename}>
                            {item.filename}
                          </h4>
                          <span className={twMerge(
                            "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider",
                            item.match_source === "content" ? "bg-blue-50 text-blue-600 border border-blue-100" : "bg-emerald-50 text-emerald-600 border border-emerald-100"
                          )}>
                            {item.match_source === "content" ? "正文命中" : "文件名命中"}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-2">
                           <FileBox className="w-3.5 h-3.5" />
                           <span className="truncate" title={item.current_path}>{item.current_path}</span>
                        </div>

                        {item.match_source === "content" && item.snippet && (
                          <div className="text-sm text-slate-600 bg-slate-50/50 border border-slate-100 rounded-lg p-3 leading-relaxed mt-2"
                               dangerouslySetInnerHTML={{
                                 __html: item.snippet.replace(/<mark>/g, '<mark class="bg-yellow-200/60 text-yellow-900 rounded-sm px-0.5 font-medium">')
                               }}
                          />
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => handleOpenFolder(item.current_path)}
                      className="shrink-0 p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-colors opacity-0 group-hover:opacity-100"
                      title="打开所在目录"
                    >
                      <FolderOpen className="w-5 h-5" />
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
              <p className="font-medium text-slate-500">没有找到匹配的内容</p>
              <p className="text-sm mt-1">您可以尝试更换关键词或搜索范围</p>
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && data && data.items.length > 0 && (
          <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
            <span className="text-sm text-slate-500 font-medium">
              共找到 {data.total} 个匹配项
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
    </div>
  );
}