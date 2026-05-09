import { Search, Filter, ArrowUpDown } from "lucide-react";
import { CustomSelect } from "../CustomSelect";

export interface FileFilterBarProps {
  keyword: string;
  extension: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  onKeywordChange: (keyword: string) => void;
  onExtensionChange: (extension: string) => void;
  onSortByChange: (sortBy: string) => void;
  onSortOrderToggle: () => void;
}

export function FileFilterBar({
  keyword,
  extension,
  sortBy,
  sortOrder,
  onKeywordChange,
  onExtensionChange,
  onSortByChange,
  onSortOrderToggle
}: FileFilterBarProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/60 p-5 mb-6 shadow-sm shrink-0 flex flex-wrap gap-4 items-center">
      <div className="relative flex-1 min-w-[240px]">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-slate-400" />
        </div>
        <input
          type="text"
          value={keyword}
          onChange={(e) => onKeywordChange(e.target.value)}
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
          onChange={(e) => onExtensionChange(e.target.value)}
          placeholder="扩展名 (如 .pdf)"
          className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400"
        />
      </div>

      <div className="h-8 w-px bg-slate-200 hidden sm:block"></div>

      <div className="relative flex items-center w-40">
        <CustomSelect
          value={sortBy}
          onChange={onSortByChange}
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
        onClick={onSortOrderToggle}
        className="px-4 py-2.5 border border-slate-200 bg-white rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors flex items-center gap-2 shadow-sm"
      >
        {sortOrder === "asc" ? "↑ 升序" : "↓ 降序"}
      </button>
    </div>
  );
}