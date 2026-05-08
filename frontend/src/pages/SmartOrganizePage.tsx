import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { createOrganizePlan, getOrganizePlanPreview, acceptOrganizePlan, rejectOrganizePlan, getAiTask } from "../services/api";
import { BrainCircuit, Loader2, ListChecks, CheckCircle2, Play, Settings, AlertCircle, FileBox, Archive, FolderTree, XCircle, ArrowRight, ShieldAlert } from "lucide-react";
import toast from "react-hot-toast";
import { ExcludeDirsModal } from "../components/ExcludeDirsModal";
import { CustomSelect } from "../components/CustomSelect";

export default function SmartOrganizePage() {
  const queryClient = useQueryClient();
  const [archiveRoot, setArchiveRoot] = useState(() => localStorage.getItem("fs_last_archive_root") || "D:/Archive");
  const [scope, setScope] = useState("all");
  const [minConfidence, setMinConfidence] = useState<number | string>(0.65);
  const [showExcludeModal, setShowExcludeModal] = useState(false);
  const [taskId, setTaskId] = useState<number | null>(
    () => {
        const saved = localStorage.getItem("fs_task_id");
        if (!saved) return null;
        const val = parseInt(saved);
        if (isNaN(val)) {
            localStorage.removeItem("fs_task_id");
            return null;
        }
        return val;
    }
  );
  const [planId, setPlanId] = useState<number | null>(
    () => {
        const saved = localStorage.getItem("fs_plan_id");
        if (!saved) return null;
        const val = parseInt(saved);
        if (isNaN(val)) {
            localStorage.removeItem("fs_plan_id");
            return null;
        }
        return val;
    }
  );

  // Sync taskId to localStorage
  useEffect(() => {
    if (taskId !== null) {
      localStorage.setItem("fs_task_id", taskId.toString());
    } else {
      localStorage.removeItem("fs_task_id");
    }
  }, [taskId]);

  // Sync planId to localStorage
  useEffect(() => {
    if (planId !== null) {
      localStorage.setItem("fs_plan_id", planId.toString());
    } else {
      localStorage.removeItem("fs_plan_id");
    }
  }, [planId]);

  const planMutation = useMutation({
    mutationFn: () => createOrganizePlan(scope, typeof minConfidence === "number" ? minConfidence : parseFloat(minConfidence) || 0),
    onSuccess: (data) => {
      setTaskId(data.task_id);
      localStorage.setItem("fs_last_archive_root", archiveRoot);
      toast.success("AI 分类任务已提交后台处理");
    },
    onError: (err: any) => toast.error(`生成失败: ${err.message}`)
  });

  const { data: task } = useQuery({
    queryKey: ["ai-task", taskId],
    queryFn: () => getAiTask(taskId!),
    enabled: taskId !== null && planId === null,
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      if (s === "pending" || s === "running") return 1000;
      return false;
    }
  });

  // Safely update planId outside of rendering phase
  useEffect(() => {
    if (task?.status === "completed" && task?.result_ref_id && planId === null) {
      setPlanId(task.result_ref_id);
    }
  }, [task, planId]);

  const { data: planData } = useQuery({
    queryKey: ["organize-plan", planId],
    queryFn: () => getOrganizePlanPreview(planId!),
    enabled: planId !== null,
  });

  const acceptMutation = useMutation({
    mutationFn: () => acceptOrganizePlan(planId!),
    onSuccess: () => {
      toast.success("整理方案已成功转化为实际移动建议！");
      setTaskId(null);
      setPlanId(null);
    },
    onError: (err: any) => toast.error(`确认失败: ${err.message}`)
  });

  const rejectMutation = useMutation({
    mutationFn: () => rejectOrganizePlan(planId!),
    onSuccess: () => {
      toast.success("已拒绝此整理方案，释放所有分类建议");
      setTaskId(null);
      setPlanId(null);
    },
    onError: (err: any) => toast.error(`拒绝失败: ${err.message}`)
  });

  // Cleanup on task failure
  useEffect(() => {
    if (task?.status === "failed" || task?.status === "rate_limited") {
      setTaskId(null);
      setPlanId(null);
    }
  }, [task?.status]);

  const isRunning = task?.status === "running" || task?.status === "pending" || planMutation.isPending;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 animation-fade-in flex flex-col min-h-0">
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
            onClick={() => planMutation.mutate()}
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
               <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
               <p className="text-rose-700 font-semibold text-lg">{task.status === "rate_limited" ? "触发 API 限流，请稍后重试" : "分类任务执行失败"}</p>
               <p className="text-sm text-slate-500 mt-2">{task.error_message}</p>
               <button onClick={() => { setTaskId(null); localStorage.removeItem("fs_task_id"); }} className="mt-4 px-4 py-2 bg-slate-100 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors">关闭</button>
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
               <div className="flex justify-between text-xs font-semibold text-slate-500">
                 <span>{task.processed_items} 已分析</span>
                 <span>共 {task.total_items} 项</span>
               </div>
             </div>
          )}
        </div>
      )}

      {planData && (
        <div className="flex-1 overflow-hidden flex flex-col bg-white rounded-2xl border border-slate-200/60 shadow-sm relative">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/80 sticky top-0 z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
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

          <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 space-y-8">
            {Object.entries(planData.groups || {}).map(([dir, items]: [string, any]) => (
              <div key={dir} className="border border-slate-200 rounded-2xl overflow-hidden">
                <div className="bg-slate-50 px-5 py-3 border-b border-slate-200 flex items-center gap-3">
                  <FolderTree className="w-5 h-5 text-blue-500" />
                  <h4 className="font-semibold text-slate-800 text-base truncate min-w-0">{dir}</h4>
                  <span className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-xs font-bold text-slate-500">
                    {items.length} 个文件
                  </span>
                </div>
                <div className="divide-y divide-slate-100">
                  {items.map((item: any) => (
                    <div key={item.item_id} className="p-4 hover:bg-slate-50/50 transition-colors">
                      <div className="flex items-start gap-3">
                        <FileBox className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                        <div className="min-w-0 flex-1">
                          <div className="font-medium text-slate-700 truncate" title={item.source_path}>
                            {item.source_path.split(/[/\\]/).pop()}
                          </div>
                          <div className="flex items-center gap-2 mt-1 text-xs text-slate-500 min-w-0">
                            <span className="truncate max-w-[40%]" title={item.source_path}>{item.source_path}</span>
                            <ArrowRight className="w-3 h-3 text-emerald-500 shrink-0" />
                            <span className="text-emerald-600 truncate font-medium flex-1">{item.target_path}</span>
                          </div>
                          <div className="mt-2 flex flex-wrap items-center gap-2">
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-600 border border-blue-100">
                              置信度: {(item.confidence * 100).toFixed(0)}%
                            </span>
                            <span className="text-xs text-slate-600 bg-white border border-slate-200 px-2 py-0.5 rounded shadow-sm break-all max-w-full">
                              {item.reason || "无解释"}
                            </span>
                            {item.directory_status === "proposed_new" && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-600 border border-amber-200">
                                拟建新目录
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
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
