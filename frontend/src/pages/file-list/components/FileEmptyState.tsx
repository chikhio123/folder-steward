import { Database } from "lucide-react";

export function FileEmptyState() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20">
      <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
        <Database className="w-8 h-8 text-slate-300" />
      </div>
      <p className="font-medium text-slate-500">没有找到匹配的文件</p>
      <p className="text-sm mt-1">您可以尝试更改搜索词或清理筛选器</p>
    </div>
  );
}