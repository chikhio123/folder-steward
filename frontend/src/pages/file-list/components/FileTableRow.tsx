import { Clock, FolderOpen } from "lucide-react";
import { twMerge } from "tailwind-merge";
import { formatSize } from "../../../utils/format";
import { FileIcon } from "../../../components/ui/FileIcon";
import type { FileRecord } from "../../../types";

export interface FileTableRowProps {
  file: FileRecord;
  onSelect: (file: FileRecord) => void;
  onOpenFolder: (path: string) => void;
}

export function FileTableRow({ file, onSelect, onOpenFolder }: FileTableRowProps) {
  return (
    <div
      onClick={() => onSelect(file)}
      className="grid grid-cols-[1fr_minmax(80px,100px)_minmax(100px,120px)_minmax(140px,160px)_100px_40px] gap-4 items-center px-6 py-3.5 hover:bg-slate-50/50 transition-colors group cursor-pointer"
    >
      <div className="flex flex-col min-w-0 gap-0.5">
        <div className="flex items-center gap-3 min-w-0">
          <FileIcon ext={file.extension} />
          <span className="text-sm font-medium text-slate-700 truncate" title={file.filename}>
            {file.filename}
          </span>
        </div>
        <span className="text-[11px] text-slate-400 truncate pl-8" title={file.current_path}>
          {file.current_path}
        </span>
      </div>
      <div className="text-sm text-slate-500 truncate">
        {file.extension ? file.extension.toLowerCase() : "未知"}
      </div>
      <div className="text-sm text-slate-600 text-center tabular-nums font-medium">
        {formatSize(file.size_bytes)}
      </div>
      <div className="text-xs text-slate-500 flex items-center gap-1.5 tabular-nums">
        <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        {file.modified_at ? file.modified_at.slice(0, 16).replace("T", " ") : "-"}
      </div>
      <div className="flex justify-center">
        <span className={twMerge(
          "px-2.5 py-1 rounded-lg text-[11px] font-semibold border tracking-wide uppercase",
          file.status === "active"
            ? "bg-emerald-50 text-emerald-700 border-emerald-200/60"
            : "bg-slate-50 text-slate-500 border-slate-200"
        )}>
          {file.status}
        </span>
      </div>
      <div className="flex justify-end">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onOpenFolder(file.current_path);
          }}
          className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
          title="打开所在目录"
        >
          <FolderOpen className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}