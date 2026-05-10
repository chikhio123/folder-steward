import { Save, Loader2, FolderArchive, ShieldAlert, FileDigit, EyeOff, Bot, Key, Link2, RefreshCw, Plus, Trash2, FolderPlus } from "lucide-react";
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { Select } from "../../components/ui/Select";
import { PathTreeView, buildPathTree } from '../../components/common/PathTreeView';
import { useSettings } from './hooks/useSettings';

export default function SettingsPage() {
  const { state, actions } = useSettings();
  const { values, profiles, activeProfileId, availableModels, isFetchingModels, showDeleteConfirm, isLoading } = state;
  const { 
    setValues, 
    setShowDeleteConfirm, 
    fetchModels, 
    updateMutation,
    handleRemoveExcludePath,
    handleAddExcludePath,
    handleProfileChange,
    handleAddProfile,
    handleDeleteProfile,
    confirmDeleteProfile
  } = actions;

  const generalFields = [
    { key: "archive_root", label: "默认归档目录", desc: "整理建议生成的默认目标文件夹路径", type: "text", placeholder: "例如：D:/Archive", icon: FolderArchive },
    { key: "scan_hidden_files", label: "扫描隐藏文件", desc: "是否将以点 (.) 开头的隐藏文件纳入索引", type: "select", options: ["true", "false"], icon: EyeOff },
    { key: "max_file_size_for_hash", label: "Hash 计算上限 (字节)", desc: "超过此大小的文件将跳过 SHA-256 哈希计算以节省时间", type: "number", icon: FileDigit },
    { key: "skip_system_directories", label: "跳过系统目录", desc: "自动跳过 Windows/System32 等敏感目录以保护系统安全", type: "select", options: ["true", "false"], icon: ShieldAlert },
  ];

  const aiFields = [
    { key: "llm_profile_name", label: "配置名称", desc: "给当前这套配置起个名字", type: "text", placeholder: "例如：OpenAI 官方、DeepSeek 中转", icon: FileDigit },
    { key: "llm_provider", label: "AI 引擎", desc: "选择大模型接口的请求格式，兼容不同中转或本地代理", type: "select", options: ["mock", "openai-response-format", "openai-raw", "anthropic-messages"], icon: Bot },
    { key: "llm_api_key", label: "API Key", desc: "大模型接口密钥 (如使用 mock 引擎可留空)", type: "password", placeholder: "sk-...", icon: Key },
    { key: "llm_base_url", label: "Base URL", desc: "接口基础地址，用于支持兼容 OpenAI 格式的其他厂商或本地模型", type: "text", placeholder: "https://api.openai.com/v1", icon: Link2 },
    { key: "llm_model", label: "Model Name", desc: "使用的具体模型名称", type: "text", placeholder: "gpt-4o-mini", icon: Bot },
  ];

  const renderField = (f: any) => (
    <div key={f.key} className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-8 pb-8 border-b border-slate-100 last:border-0 last:pb-0">
      <div className="sm:w-1/3 shrink-0">
        <label className="flex items-center gap-2 text-sm font-semibold text-slate-800 mb-1.5">
          <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
            <f.icon className="w-4 h-4" />
          </div>
          {f.label}
        </label>
        <p className="text-xs text-slate-500 leading-relaxed pr-4">
          {f.desc}
        </p>
      </div>
      <div className="flex-1 max-w-md mt-1 sm:mt-0">
        {f.type === "select" ? (
          <Select
            value={values[f.key] ?? ""}
            onChange={(value) => setValues((v: Record<string, string>) => ({ ...v, [f.key]: value }))}
            options={(f.options || []).map((o: string) => ({
              value: o,
              label: o === "true" ? "开启 (True)" : o === "false" ? "关闭 (False)" : o
            }))}
            className="w-full"
          />
        ) : (
          <>
            <div className={f.key === "llm_model" ? "flex items-center gap-2" : ""}>
              <input
                type={f.type}
                value={values[f.key] ?? ""}
                onChange={(e) => setValues((v: Record<string, string>) => ({ ...v, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                className="flex-1 w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400 shadow-sm"
              />
              {f.key === "llm_model" && (
                <button
                  onClick={fetchModels}
                  disabled={isFetchingModels}
                  className="shrink-0 flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-xl text-sm font-medium transition-all disabled:opacity-50"
                  title="拉取可用模型"
                >
                  {isFetchingModels ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                  拉取
                </button>
              )}
            </div>
            {f.key === "llm_base_url" && (
              <div className="mt-1.5 px-3 py-1.5 bg-slate-100/80 rounded-lg border border-slate-200/60 text-xs font-mono text-slate-500 overflow-x-auto">
                {(values[f.key] || "").replace(/\/$/, "") + (!(values[f.key] || "").replace(/\/$/, "").endsWith("/v1") ? "/v1" : "") + "/chat/completions"}
              </div>
            )}
            {f.key === "llm_model" && availableModels.length > 0 && (
              <div className="mt-2">
                <Select
                  value={values[f.key] ?? ""}
                  onChange={(value) => setValues((v: Record<string, string>) => ({ ...v, [f.key]: value }))}
                  options={availableModels.map(m => ({ value: m, label: m }))}
                  placeholder="-- 请选择下拉模型 --"
                  className="w-full"
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto animation-fade-in flex flex-col relative min-h-full">
      {/* 背景光晕 */}
      <div className="absolute top-[10%] left-[-10%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="mb-6 shrink-0 relative z-10">
        <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-400 tracking-tight pb-1">应用设置</h2>
        <p className="text-slate-500 mt-1 font-medium">全局配置参数，定制您的文件扫描和整理偏好。</p>
      </div>

      <div className="pb-8 space-y-6 relative z-10">
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 p-8 shadow-sm hover:shadow-md transition-all duration-300">
          <h3 className="text-lg font-bold text-slate-800 mb-6">常规设置</h3>
          {isLoading ? (
            <div className="flex flex-col items-center justify-center text-slate-400 py-10 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p>加载设置中...</p>
            </div>
          ) : (
            <div className="space-y-8">
              {generalFields.map(renderField)}
            </div>
          )}
        </div>

        <div className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 p-8 shadow-sm hover:shadow-md transition-all duration-300">
          <h3 className="text-lg font-bold text-slate-800 mb-6">AI 排除目录</h3>
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-8 pb-8">
              <div className="sm:w-1/3 shrink-0">
                <label className="flex items-center gap-2 text-sm font-semibold text-slate-800 mb-1.5">
                  <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                  AI 排除目录
                </label>
                <p className="text-xs text-slate-500 leading-relaxed pr-4">
                  配置的目录及其子目录将被 AI 完全忽略，保证隐私安全。
                </p>
              </div>
              <div className="flex-1 max-w-md mt-1 sm:mt-0">
                <div className="bg-white/60 backdrop-blur-md border border-slate-200/60 rounded-xl p-4 shadow-sm hover:bg-white/80 hover:border-slate-300/80 transition-all">
                  <div className="flex flex-col gap-1 mb-3 max-h-[300px] overflow-y-auto custom-scrollbar">
                    {(() => {
                      const paths = (values.ai_exclude_paths || "").split("\n").map(p => p.trim()).filter(p => p);
                      if (paths.length === 0) {
                        return (
                          <div className="w-full text-center py-6 text-slate-400 text-sm border-2 border-dashed border-slate-200/60 rounded-lg">
                            未配置排除目录
                          </div>
                        );
                      }

                      const tree = buildPathTree(paths);
                      return tree.map(node => (
                        <PathTreeView key={node.path} node={node} onRemove={handleRemoveExcludePath} />
                      ));
                    })()}
                  </div>

                  <button
                    type="button"
                    onClick={handleAddExcludePath}
                    className="w-full py-2.5 flex items-center justify-center gap-2 text-sm font-semibold text-blue-600 bg-blue-50/50 hover:bg-blue-100/50 border border-blue-200/50 rounded-lg transition-colors border-dashed"
                  >
                    <FolderPlus className="w-4 h-4" />
                    添加排除目录
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 p-8 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-800">AI 引擎配置</h3>
            {!isLoading && (
              <div className="flex items-center gap-2">
                <Select
                  value={activeProfileId}
                  onChange={(value) => handleProfileChange(value)}
                  options={profiles.map(p => ({
                    value: p.id,
                    label: p.name || "未命名配置"
                  }))}
                  className="w-48"
                />
                <button
                  onClick={handleAddProfile}
                  className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="新建配置"
                >
                  <Plus className="w-4 h-4" />
                </button>
                {profiles.length > 1 && (
                  <button
                    onClick={handleDeleteProfile}
                    className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg transition-colors"
                    title="删除当前配置"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
          </div>
          {isLoading ? (
            <div className="flex flex-col items-center justify-center text-slate-400 py-10 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
          ) : (
            <div className="space-y-8">
              {aiFields.map(renderField)}
            </div>
          )}
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-2"
          >
            {updateMutation.isPending ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> 保存中</>
            ) : (
              <><Save className="w-4 h-4" /> 保存所有设置</>
            )}
          </button>
        </div>
      </div>

      <ConfirmModal
        isOpen={showDeleteConfirm}
        title="删除配置"
        message="确定要删除当前 AI 引擎配置吗？"
        confirmText="删除"
        confirmVariant="danger"
        onConfirm={confirmDeleteProfile}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
