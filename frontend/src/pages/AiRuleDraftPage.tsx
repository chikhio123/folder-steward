import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { previewRuleDraft, acceptRuleDraft, listRules, updateRule, deleteRule } from "../services/api";
import { Wand2, Save, FileBox, AlertCircle, CheckCircle2, ArrowRight, Loader2, Sparkles, Settings2, Trash2 } from "lucide-react";
import { twMerge } from "tailwind-merge";
import toast from "react-hot-toast";
import { useDraftContext } from "../contexts/DraftContext";

export default function AiRuleDraftPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"create" | "manage">("create");

  const {
    prompt,
    setPrompt,
    draftId,
    setDraftId,
    draftMutation,
    handleGenerate,
    handleCancel,
    handleReset,
  } = useDraftContext();

  const acceptMutation = useMutation({
    mutationFn: () => acceptRuleDraft(draftId!),
    onSuccess: () => {
      toast.success("规则已保存并生效，后台正在刷新整理建议！");
      setDraftId(null);
      setPrompt("");
      // queryClient.invalidateQueries(...) is handled by the backend trigger effectively
    },
    onError: (err: any) => {
      toast.error(`保存失败: ${err.message}`);
    }
  });

  const { data: previewData, isLoading: isPreviewLoading } = useQuery({
    queryKey: ["rule-draft-preview", draftId],
    queryFn: () => previewRuleDraft(draftId!),
    enabled: !!draftId && draftMutation.isSuccess && draftMutation.data?.status === "validated",
  });

  const draft = draftMutation.data;

  // Rules Management
  const { data: rulesList, isLoading: isRulesLoading } = useQuery({
    queryKey: ["rules", "all"],
    queryFn: () => listRules(false),
    enabled: activeTab === "manage",
  });

  const toggleRuleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number, enabled: boolean }) => updateRule(id, { enabled: enabled ? 1 : 0 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules", "all"] });
      toast.success("规则状态已更新");
    },
    onError: (err: any) => toast.error(`状态更新失败: ${err.message}`)
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (id: number) => deleteRule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules", "all"] });
      toast.success("规则已永久删除");
    },
    onError: (err: any) => toast.error(`删除失败: ${err.message}`)
  });

  return (
    <div className="max-w-4xl mx-auto animation-fade-in flex flex-col h-full relative">
      {/* 背景光晕 */}
      <div className="absolute top-[-10%] right-[-10%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="mb-6 shrink-0 relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-400 tracking-tight flex items-center gap-2 pb-1">
            <Sparkles className="w-8 h-8 text-blue-500 shrink-0" />
            AI 自动化规则
          </h2>
          <p className="text-slate-500 mt-1 font-medium">让 AI 把您的整理习惯转化成自动化规则，一劳永逸。</p>
        </div>

        {/* 苹果风 Segmented Control */}
        <div className="flex bg-slate-200/50 p-1 rounded-xl w-fit">
          <button
            onClick={() => setActiveTab("create")}
            className={twMerge(
              "px-5 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2",
              activeTab === "create"
                ? "bg-white text-blue-600 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            <Wand2 className="w-4 h-4" />
            写新规则
          </button>
          <button
            onClick={() => setActiveTab("manage")}
            className={twMerge(
              "px-5 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2",
              activeTab === "manage"
                ? "bg-white text-blue-600 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            <Settings2 className="w-4 h-4" />
            管理规则
            {rulesList && rulesList.length > 0 && (
              <span className={twMerge(
                "px-1.5 py-0.5 rounded-md text-[10px]",
                activeTab === "manage" ? "bg-blue-100 text-blue-700" : "bg-slate-200 text-slate-500"
              )}>
                {rulesList.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {activeTab === "create" ? (
        <div className="flex-1 overflow-y-auto pb-8 relative z-10 flex flex-col min-h-0">
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 p-6 mb-6 shadow-sm hover:shadow-md transition-all duration-300 shrink-0">
        <label className="block text-sm font-semibold text-slate-700 mb-3">
          描述您的整理意图
        </label>
        <div className="flex flex-col gap-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="例如：把包含“发票”或“报销”的文件都移动到 Finance/Receipts 目录下..."
            className="w-full bg-white/60 backdrop-blur-md border border-slate-200/60 text-slate-800 rounded-xl px-4 py-3 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all placeholder:text-slate-400/80 min-h-[100px] resize-y shadow-sm hover:bg-white/80 hover:border-slate-300/80 hover:shadow"
            disabled={draftMutation.isPending}
          />
          <div className="flex justify-end gap-3">
            {draftMutation.isPending && (
              <button
                onClick={handleCancel}
                className="px-5 py-2.5 text-sm font-semibold text-rose-600 bg-rose-50 hover:bg-rose-100 hover:shadow-md shadow-rose-600/20 rounded-xl transition-all"
              >
                停止生成
              </button>
            )}
            <button
              onClick={handleGenerate}
              disabled={!prompt.trim() || draftMutation.isPending}
              className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-2"
            >
              {draftMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
              AI 生成草案
            </button>
          </div>
        </div>
      </div>

      {draft && (
        <div className="flex-1 overflow-y-auto pb-8 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/60 p-6 shadow-sm transition-all duration-300">
            <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              草案解析结果
              {draft.status === "validated" ? (
                <span className="px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/60 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> 校验通过
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200/60 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" /> 校验失败
                </span>
              )}
            </h3>

            {draft.status === "failed" ? (
              <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl text-sm text-rose-700">
                <strong className="block mb-1">目录安全校验拦截：</strong>
                {draft.validation_error}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="text-xs font-semibold text-slate-500 mb-1">规则名称</div>
                    <div className="text-sm text-slate-800 font-medium">{draft.name}</div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="text-xs font-semibold text-slate-500 mb-1">匹配类型</div>
                    <div className="text-sm text-slate-800 font-medium">{draft.rule_type}</div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 col-span-2">
                    <div className="text-xs font-semibold text-slate-500 mb-1">关键词模式</div>
                    <div className="text-sm text-blue-600 font-mono bg-blue-50 px-2 py-1 rounded inline-block border border-blue-100">{draft.pattern}</div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 col-span-2">
                    <div className="text-xs font-semibold text-slate-500 mb-1">目标目录</div>
                    <div className="text-sm text-emerald-600 font-mono bg-emerald-50 px-2 py-1 rounded inline-block border border-emerald-100">{draft.target_dir}</div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 col-span-2">
                    <div className="text-xs font-semibold text-slate-500 mb-1">AI 解释</div>
                    <div className="text-sm text-slate-600">{draft.reason}</div>
                  </div>
                </div>

                <div className="pt-4 flex justify-end gap-3 border-t border-slate-100">
                  <button
                    onClick={() => { draftMutation.reset(); setDraftId(null); setPrompt(""); }}
                    className="px-5 py-2.5 text-sm font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 hover:shadow-sm rounded-xl transition-all"
                  >
                    丢弃草案
                  </button>
                  <button
                    onClick={() => handleReset()}
                    className="px-5 py-2.5 text-sm font-semibold text-blue-600 bg-blue-50 border border-blue-200 hover:bg-blue-100 hover:shadow-sm rounded-xl transition-all"
                  >
                    重新生成
                  </button>
                  <button
                    onClick={() => acceptMutation.mutate()}
                    disabled={acceptMutation.isPending}
                    className="px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl text-sm font-semibold shadow-md shadow-emerald-500/20 hover:shadow-lg hover:shadow-emerald-500/30 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-2"
                  >
                    {acceptMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    保存为正式规则
                  </button>
                </div>
              </div>
            )}
          </div>

          {draft.status === "validated" && (
            <div className="bg-white rounded-2xl border border-slate-200/60 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-slate-800 mb-4">预览命中结果</h3>
              {isPreviewLoading ? (
                <div className="py-8 flex flex-col items-center justify-center text-slate-400 space-y-3">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                  <p className="text-sm">正在检索受影响的文件...</p>
                </div>
              ) : previewData?.items?.length ? (
                <div className="space-y-2">
                  <div className="text-sm text-slate-500 mb-3">找到 {previewData.matched_count} 个符合条件的文件（示例）：</div>
                  {previewData.items.map((item: any, idx: number) => (
                    <div key={idx} className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <FileBox className="w-4 h-4 text-slate-400 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-700 truncate">{item.filename}</div>
                        <div className="flex items-center gap-1.5 text-xs mt-1">
                          <span className="text-slate-400 truncate max-w-[40%]">{item.current_path}</span>
                          <ArrowRight className="w-3 h-3 text-emerald-500 shrink-0" />
                          <span className="text-emerald-600 font-medium truncate flex-1">{item.target_path}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-sm text-slate-400 bg-slate-50 border border-slate-100 rounded-xl border-dashed">
                  当前规则没有命中任何文件
                </div>
              )}
            </div>
          )}
        </div>
      )}
      </div>
      ) : (
        <div className="flex-1 overflow-y-auto pb-8 relative z-10 flex flex-col min-h-0">
          {isRulesLoading ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p>加载规则列表中...</p>
            </div>
          ) : rulesList && rulesList.length > 0 ? (
            <div className="space-y-4">
              {rulesList.map((r: any) => (
                <div key={r.id} className={twMerge(
                  "bg-white/80 backdrop-blur-xl rounded-2xl border p-5 shadow-sm transition-all duration-300",
                  r.enabled ? "border-slate-200/60" : "border-slate-100 opacity-60 bg-slate-50/50"
                )}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-bold text-slate-800 truncate" title={r.name}>{r.name}</h3>
                        {!r.enabled && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-200 text-slate-500 tracking-wider">
                            已停用
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-sm mb-3 flex-wrap">
                        <span className="px-2 py-1 rounded bg-slate-100 text-slate-600 font-medium">
                          {r.rule_type === "extension" ? "按后缀名" : r.rule_type === "filename_keyword" ? "按文件名" : "按正文内容"}
                        </span>
                        <span className="text-slate-400">匹配</span>
                        <span className="font-mono text-blue-600 bg-blue-50 px-2 py-1 rounded border border-blue-100 break-all">
                          {r.pattern}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-slate-500">移动至</span>
                        <ArrowRight className="w-4 h-4 text-emerald-500" />
                        <span className="font-mono text-emerald-600 bg-emerald-50 px-2 py-1 rounded border border-emerald-100 break-all font-medium">
                          {r.target_dir}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-3 shrink-0">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={r.enabled}
                          onChange={(e) => toggleRuleMutation.mutate({ id: r.id, enabled: e.target.checked })}
                          disabled={toggleRuleMutation.isPending}
                        />
                        <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                      </label>

                      <button
                        onClick={() => {
                          if (window.confirm("确定要永久删除这条规则吗？")) {
                            deleteRuleMutation.mutate(r.id);
                          }
                        }}
                        disabled={deleteRuleMutation.isPending}
                        className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors mt-auto"
                        title="删除规则"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20">
              <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                <Settings2 className="w-8 h-8 text-slate-300" />
              </div>
              <p className="font-medium text-slate-500">暂无任何自动化规则</p>
              <p className="text-sm mt-1">请前往“写新规则”页面，让 AI 帮您生成</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}