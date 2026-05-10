import { BrainCircuit, Loader2, ListChecks, CheckCircle2, Play, Settings, AlertCircle, Archive, XCircle, ShieldAlert } from "lucide-react";
import { ExcludeDirsModal } from "../components/common/ExcludeDirsModal";
import { CustomSelect } from "../components/common/CustomSelect";
import { useSmartOrganize } from './smart-organize/hooks/useSmartOrganize';
import { PlanPreviewGroup } from './smart-organize/components/PlanPreviewGroup';

export default function SmartOrganizePage() {
  const { state, actions, mutations } = useSmartOrganize();
  const { archiveRoot, scope, minConfidence, showExcludeModal, planId, isRunning, task, planData } = state;
  const { setArchiveRoot, setScope, setMinConfidence, setShowExcludeModal, setTaskId } = actions;
  const { planMutation, cancelMutation, acceptMutation, rejectMutation } = mutations;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 animation-fade-in flex flex-col relative min-h-full">
      <div className="mb-8 shrink-0">
        <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-400 tracking-tight flex items-center gap-2 pb-1">
          <BrainCircuit className="w-8 h-8 text-blue-500 shrink-0" />
          AI 智能整理大盘
        </h2>
        <p className="text-slate-500 mt-1 font-medium">
          将未分类的文件批量丢给大模型，生成结构化的分组整理方案。
        </p>
      </div>

      <div className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 p-6 mb-6 shadow-sm hover:shadow-md transition-all duration-300 shrink-0">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
              <Archive className="w-4 h-4 text-blue-500" /> 归档根目录
            </label>
            <input
              type="text"
              value={archiveRoot}
              onChange={(e) => setArchiveRoot(e.target.value)}
              placeholder="例如：D:/Archive"
              disabled={isRunning}
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
              <ListChecks className="w-4 h-4 text-blue-500" /> 处理范围
            </label>
            <CustomSelect
              value={scope}
              onChange={(val) => setScope(val)}
              disabled={isRunning}
              options={[
                { value: "others", label: "仅未识别分类的文件 (Others)" },
                { value: "all", label: "库中所有未操作的文件" }
              ]}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
              <Settings className="w-4 h-4 text-blue-500" /> 最低采纳置信度
            </label>
            <input
              type="number"
              min="0" max="1" step="0.05"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              disabled={isRunning}
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
        </div>
        <div className="mt-6 flex justify-end">
          <button
            onClick={() => planMutation.mutate({
              scope,
              minConfidence: typeof minConfidence === "number" ? minConfidence : parseFloat(minConfidence as string) || 0,
              archiveRoot
            })}
            disabled={isRunning || !!planId}
            className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-2"
          >
            {planMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" fill="currentColor" />}
            生成整理方案
          </button>
        </div>
      </div>

      {task && !planId && (
        <div className="bg-white rounded-2xl border border-slate-200/60 p-8 mb-6 shadow-sm flex flex-col items-center justify-center space-y-4 py-16">
          {task.status === "failed" || task.status === "rate_limited" ? (
             <div className="text-center">
               {task.error_message === "Cancelled by user" ? (
                 <>
                   <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-3" />
                   <p className="text-amber-700 font-semibold text-lg">AI 任务已由用户取消</p>
                   <p className="text-sm text-slate-500 mt-2">没有文件被移动，您可以调整参数后重新开始。</p>
                 </>
               ) : (
                 <>
                   <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
                   <p className="text-rose-700 font-semibold text-lg">{task.status === "rate_limited" ? "触发 API 限流，请稍后重试" : "分类任务执行失败"}</p>
                   <p className="text-sm text-slate-500 mt-2">{task.error_message}</p>
                 </>
               )}
               <button onClick={() => { setTaskId(null); localStorage.removeItem("fs_task_id"); }} className="mt-4 px-4 py-2 bg-slate-100 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors">关闭并重置</button>
             </div>
          ) : (
             <div className="text-center w-full max-w-md">
               <BrainCircuit className="w-12 h-12 text-blue-400 mx-auto mb-4 animate-pulse" />
               <h3 className="text-lg font-bold text-slate-800 mb-2">AI 正在深度阅读并分类文件</h3>
               <p className="text-sm text-slate-500 mb-6">正在分析正文特征与上下文...</p>

               <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden ring-1 ring-inset ring-slate-200/50 mb-2">
                 <div
                   className="bg-blue-500 h-full rounded-full transition-all duration-500 relative"
                   style={{ width: task.total_items > 0 ? `${(task.processed_items / task.total_items) * 100}%` : "0%" }}
                 >
                   <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                 </div>
               </div>
               <div className="flex justify-between text-xs font-semibold text-slate-500 mb-8">
                 <span>{task.processed_items} 已分析</span>
                 <span>共 {task.total_items} 项</span>
               </div>

               <button
                 onClick={() => cancelMutation.mutate()}
                 disabled={cancelMutation.isPending}
                 className="px-4 py-2 border border-slate-200 text-slate-500 rounded-xl text-sm font-semibold hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 transition-all flex items-center gap-2 mx-auto disabled:opacity-50"
               >
                 {cancelMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                 {cancelMutation.isPending ? "正在停止..." : "取消任务"}
               </button>
             </div>
          )}
        </div>
      )}

      {planData && (
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm relative flex flex-col mb-8">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/80 sticky top-0 z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-t-2xl">
            <div>
              <h3 className="text-lg font-bold text-slate-800">{planData.title}</h3>
              <p className="text-xs text-slate-500 mt-0.5">请审查 AI 自动分组结果，确认无误后转化为执行建议。</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => setShowExcludeModal(true)}
                className="px-4 py-2 flex items-center gap-1.5 text-sm font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl transition-colors"
              >
                <ShieldAlert className="w-4 h-4 text-slate-400" /> 管理排除目录
              </button>
              <button
                onClick={() => rejectMutation.mutate()}
                disabled={rejectMutation.isPending || acceptMutation.isPending}
                className="px-4 py-2 flex items-center gap-1.5 text-sm font-semibold text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-xl transition-colors disabled:opacity-50"
              >
                <XCircle className="w-4 h-4" /> 拒绝并抛弃
              </button>
              <button
                onClick={() => acceptMutation.mutate()}
                disabled={acceptMutation.isPending || rejectMutation.isPending}
                className="px-5 py-2 flex items-center gap-1.5 text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm shadow-emerald-600/20 rounded-xl transition-colors disabled:opacity-50"
              >
                {acceptMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                同意计划
              </button>
            </div>
          </div>

          <div className="p-6 space-y-8">
            {Object.entries(planData.groups || {}).map(([dir, items]: [string, any]) => (
              <PlanPreviewGroup dir={dir} items={items} key={dir} />
            ))}
          </div>
        </div>
      )}

      <ExcludeDirsModal
        isOpen={showExcludeModal}
        onClose={() => setShowExcludeModal(false)}
        planGroups={planData?.groups}
      />
    </div>
  );
}
