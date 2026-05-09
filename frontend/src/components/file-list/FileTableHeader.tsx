import { ChevronUp, ChevronDown } from "lucide-react";
import { twMerge } from "tailwind-merge";

const SortIcon = ({ active, order }: { active: boolean, order: "asc" | "desc" }) => (
  <div className={twMerge(
    "flex flex-col -space-y-1 transition-all duration-200 group-hover:scale-125",
    active ? "opacity-100" : "opacity-0 group-hover:opacity-100"
  )}>
    <ChevronUp className={twMerge("w-3 h-3", active && order === "asc" ? "text-blue-600" : "text-slate-400")} strokeWidth={active && order === "asc" ? 3 : 2} />
    <ChevronDown className={twMerge("w-3 h-3", active && order === "desc" ? "text-blue-600" : "text-slate-400")} strokeWidth={active && order === "desc" ? 3 : 2} />
  </div>
);

export interface FileTableHeaderProps {
  sortBy: string;
  sortOrder: "asc" | "desc";
  onSortChange: (field: string) => void;
}

export function FileTableHeader({ sortBy, sortOrder, onSortChange }: FileTableHeaderProps) {
  return (
    <div className="grid grid-cols-[1fr_minmax(80px,100px)_minmax(100px,120px)_minmax(140px,160px)_100px_40px] gap-4 items-center px-6 py-4 border-b border-slate-100/80 bg-slate-50/40 sticky top-0 z-10 text-sm font-semibold text-slate-600 rounded-t-2xl">
      <div className="pl-2">
        <button
          onClick={() => onSortChange("filename")}
          className="flex items-center gap-1.5 hover:text-blue-600 transition-colors group"
        >
          文件名
          <SortIcon active={sortBy === "filename"} order={sortOrder} />
        </button>
      </div>
      <div>类型</div>
      <div className="flex justify-center">
        <button
          onClick={() => onSortChange("size_bytes")}
          className="flex items-center gap-1.5 hover:text-blue-600 transition-colors group"
        >
          大小
          <SortIcon active={sortBy === "size_bytes"} order={sortOrder} />
        </button>
      </div>
      <div className="flex justify-start">
        <button
          onClick={() => onSortChange("modified_at")}
          className="flex items-center gap-1.5 hover:text-blue-600 transition-colors group"
        >
          最后修改
          <SortIcon active={sortBy === "modified_at"} order={sortOrder} />
        </button>
      </div>
      <div className="text-center">状态</div>
      <div></div>
    </div>
  );
}