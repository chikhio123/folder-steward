import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createRuleDraft, previewRuleDraft, acceptRuleDraft } from "../services/api";
import { Wand2, Save, FileBox, AlertCircle, CheckCircle2, ArrowRight, Loader2, Sparkles } from "lucide-react";
import toast from "react-hot-toast";

export default function AiRuleDraftPage() {
  const [prompt, setPrompt] = useState("");
  const [draftId, setDraftId] = useState<number | null>(null);

  const draftMutation = useMutation({
    mutationFn: (variables: { prompt: string; signal?: AbortSignal }) =>
      createRuleDraft(variables.prompt, variables.signal),
    onSuccess: (data) => {
      setDraftId(data.draft_id);
      toast.success("规则草案生成成功！");
    },
    onError: (err: any) => {
      if (err.name === 'AbortError' || err.message?.includes('aborted')) {
          return; // Silent for user cancel
      }
      toast.error(`生成失败: ${err.message}`);
    }
  });

  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const handleGenerate = () => {
      const controller = new AbortController();
      setAbortController(controller);
      draftMutation.mutate({ prompt, signal: controller.signal });
  };

  const handleCancel = () => {
      if (abortController) {
          abortController.abort();
          setAbortController(null);
          toast.success("生成已中止");
      }
  };

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

  return (
    <div className="max-w-4xl mx-auto animation-fade-in flex flex-col h-full">
      <div className="mb-6 shrink-0">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <Sparkles className="w-8 h-8 text-blue-500" />
          自然语言规则生成
        </h2>
        <p className="text-slate-500 mt-1">告诉 AI 您想怎么整理文件，它会自动生成结构化的归档规则并预览受影响的文件。</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 p-6 mb-6 shadow-sm shrink-0">
        <label className="block text-sm font-semibold text-slate-700 mb-3">
          描述您的整理意图
        </label>
        <div className="flex flex-col gap-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="例如：把包含“发票”或“报销”的文件都移动到 Finance/Receipts 目录下..."
            className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400 min-h-[100px] resize-y shadow-inner"
            disabled={draftMutation.isPending}
          />
          <div className="flex justify-end gap-3">
            {draftMutation.isPending && (
              <button
                onClick={handleCancel}
                className="px-4 py-2.5 text-sm font-semibold text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
              >
                停止生成
              </button>
            )}
            <button
              onClick={handleGenerate}
              disabled={!prompt.trim() || draftMutation.isPending}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold shadow-sm shadow-blue-600/20 hover:bg-blue-700 hover:shadow-md active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-2"
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
                    onClick={() => { setDraftId(null); setPrompt(""); }}
                    className="px-5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                  >
                    丢弃草案
                  </button>
                  <button
                    onClick={() => acceptMutation.mutate()}
                    disabled={acceptMutation.isPending}
                    className="px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold shadow-sm shadow-emerald-600/20 hover:bg-emerald-700 hover:shadow-md active:translate-y-0 disabled:opacity-50 transition-all flex items-center gap-2"
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
  );
}