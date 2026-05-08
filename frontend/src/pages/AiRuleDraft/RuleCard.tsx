import { twMerge } from 'tailwind-merge';
import { ArrowRight, Trash2 } from 'lucide-react';

export default function RuleCard({ rule, onToggle, onDelete, isToggling, isDeleting }: any) {
  return (
    <div className={twMerge(
      "bg-white/80 backdrop-blur-xl rounded-2xl border p-5 shadow-sm transition-all duration-300",
      rule.enabled ? "border-slate-200/60" : "border-slate-100 opacity-60 bg-slate-50/50"
    )}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-bold text-slate-800 truncate" title={rule.name}>{rule.name}</h3>
            {!rule.enabled && (
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-200 text-slate-500 tracking-wider">
                已停用
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm mb-3 flex-wrap">
            <span className="px-2 py-1 rounded bg-slate-100 text-slate-600 font-medium">
              {rule.rule_type === "extension" ? "按后缀名" : rule.rule_type === "filename_keyword" ? "按文件名" : "按正文内容"}
            </span>
            <span className="text-slate-400">匹配</span>
            <span className="font-mono text-blue-600 bg-blue-50 px-2 py-1 rounded border border-blue-100 break-all">
              {rule.pattern}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">移动至</span>
            <ArrowRight className="w-4 h-4 text-emerald-500" />
            <span className="font-mono text-emerald-600 bg-emerald-50 px-2 py-1 rounded border border-emerald-100 break-all font-medium">
              {rule.target_dir}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-3 shrink-0">
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={rule.enabled}
              onChange={(e) => onToggle(rule.id, e.target.checked)}
              disabled={isToggling}
            />
            <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
          </label>
          <button
            onClick={() => {
              if (window.confirm("确定要永久删除这条规则吗？")) {
                onDelete(rule.id);
              }
            }}
            disabled={isDeleting}
            className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors mt-auto"
            title="删除规则"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}