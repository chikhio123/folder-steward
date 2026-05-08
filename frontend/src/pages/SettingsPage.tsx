import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSettings, updateSettings, getAvailableModels } from "../services/api";
import { useState, useEffect } from "react";
import { Save, Loader2, FolderArchive, ShieldAlert, FileDigit, EyeOff, Bot, Key, Link2, RefreshCw, Plus, Trash2 } from "lucide-react";
import toast from "react-hot-toast";

interface ApiProfile {
  id: string;
  name: string;
  provider: string;
  api_key: string;
  base_url: string;
  model: string;
}

const defaultSettings = {
  archive_root: "",
  scan_hidden_files: "false",
  max_file_size_for_hash: "104857600",
  skip_system_directories: "true",
  ai_exclude_paths: "",
  llm_provider: "mock",
  llm_api_key: "",
  llm_base_url: "",
  llm_model: "gpt-4o-mini",
};

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  
  const [values, setValues] = useState<Record<string, string>>(defaultSettings);
  const [profiles, setProfiles] = useState<ApiProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string>("");
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [isFetchingModels, setIsFetchingModels] = useState(false);

  const fetchModels = async () => {
    if (!values.llm_base_url) {
      toast.error("请先填写 Base URL");
      return;
    }
    setIsFetchingModels(true);
    try {
      const res = await getAvailableModels(values.llm_base_url, values.llm_api_key || "");
      if (res.models && res.models.length > 0) {
        setAvailableModels(res.models);
        toast.success(`成功获取 ${res.models.length} 个模型！`);
      } else {
        toast.error("未找到可用的模型列表");
      }
    } catch (err: any) {
      toast.error(`获取模型失败: ${err.message}`);
    } finally {
      setIsFetchingModels(false);
    }
  };

  useEffect(() => {
    if (data) {
      const parsedData = { ...data };
      if (parsedData.ai_exclude_paths) {
        try {
          const parsed = JSON.parse(parsedData.ai_exclude_paths);
          if (Array.isArray(parsed)) {
            parsedData.ai_exclude_paths = parsed.join("\n");
          }
        } catch (e) {}
      }

      let loadedProfiles: ApiProfile[] = [];
      let activeId = parsedData.active_llm_profile_id || "default";

      if (parsedData.llm_profiles) {
        try {
          loadedProfiles = JSON.parse(parsedData.llm_profiles);
        } catch (e) {}
      }

      if (loadedProfiles.length === 0) {
        loadedProfiles = [{
          id: "default",
          name: "默认配置",
          provider: parsedData.llm_provider || "mock",
          api_key: parsedData.llm_api_key || "",
          base_url: parsedData.llm_base_url || "",
          model: parsedData.llm_model || "gpt-4o-mini"
        }];
        activeId = "default";
      }

      setProfiles(loadedProfiles);
      setActiveProfileId(activeId);

      const activeProfile = loadedProfiles.find(p => p.id === activeId) || loadedProfiles[0];
      parsedData.llm_profile_name = activeProfile.name;
      parsedData.llm_provider = activeProfile.provider;
      parsedData.llm_api_key = activeProfile.api_key;
      parsedData.llm_base_url = activeProfile.base_url;
      parsedData.llm_model = activeProfile.model;

      setValues({ ...defaultSettings, ...parsedData });
    }
  }, [data]);

  const getCurrentProfileUpdated = () => ({
    name: values.llm_profile_name || "",
    provider: values.llm_provider,
    api_key: values.llm_api_key,
    base_url: values.llm_base_url,
    model: values.llm_model,
  });

  const handleProfileChange = (id: string) => {
    // Save current values to old profile
    const updatedProfiles = profiles.map(p =>
      p.id === activeProfileId ? { ...p, ...getCurrentProfileUpdated(), name: values.llm_profile_name || p.name } : p
    );
    setProfiles(updatedProfiles);
    setActiveProfileId(id);

    // Load new profile into values
    const newProfile = updatedProfiles.find(p => p.id === id);
    if (newProfile) {
      setValues(v => ({
        ...v,
        llm_profile_name: newProfile.name,
        llm_provider: newProfile.provider,
        llm_api_key: newProfile.api_key,
        llm_base_url: newProfile.base_url,
        llm_model: newProfile.model
      }));
    }
  };

  const handleAddProfile = () => {
    const newId = Date.now().toString();
    const newProfile: ApiProfile = {
      id: newId,
      name: `新配置 ${profiles.length + 1}`,
      provider: "mock",
      api_key: "",
      base_url: "",
      model: "gpt-4o-mini"
    };

    // Save current to existing profile first
    const updatedProfiles = profiles.map(p =>
      p.id === activeProfileId ? { ...p, ...getCurrentProfileUpdated(), name: values.llm_profile_name || p.name } : p
    );

    setProfiles([...updatedProfiles, newProfile]);
    setActiveProfileId(newId);
    setValues(v => ({
      ...v,
      llm_profile_name: newProfile.name,
      llm_provider: newProfile.provider,
      llm_api_key: newProfile.api_key,
      llm_base_url: newProfile.base_url,
      llm_model: newProfile.model
    }));
  };

  const handleDeleteProfile = () => {
    if (profiles.length <= 1) return;
    if (window.confirm("确定要删除当前配置吗？")) {
      const remaining = profiles.filter(p => p.id !== activeProfileId);
      setProfiles(remaining);
      setActiveProfileId(remaining[0].id);
      setValues(v => ({
        ...v,
        llm_profile_name: remaining[0].name,
        llm_provider: remaining[0].provider,
        llm_api_key: remaining[0].api_key,
        llm_base_url: remaining[0].base_url,
        llm_model: remaining[0].model
      }));
    }
  };

  const updateMutation = useMutation({
    mutationFn: () => {
      const finalProfiles = profiles.map(p =>
        p.id === activeProfileId ? { ...p, ...getCurrentProfileUpdated(), name: values.llm_profile_name || p.name } : p
      );

      const payload = {
        ...values,
        llm_profiles: JSON.stringify(finalProfiles),
        active_llm_profile_id: activeProfileId
      };

      let parsedAiPaths: string[] = [];
      if (payload.ai_exclude_paths) {
        parsedAiPaths = payload.ai_exclude_paths
          .split(/[,\n]/)
          .map(p => p.trim())
          .filter(p => p);
        payload.ai_exclude_paths = JSON.stringify(parsedAiPaths);
      } else {
        payload.ai_exclude_paths = "[]";
      }

      // 移除临时用于双向绑定的 name 字段，防止存入多余字段
      delete payload.llm_profile_name;

      return updateSettings(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("全局设置已成功保存！");
    },
    onError: (err) => {
      toast.error(`保存设置失败: ${err.message}`);
    }
  });

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
          <div className="relative">
            <select
              value={values[f.key] ?? ""}
              onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 appearance-none cursor-pointer transition-all shadow-sm"
            >
              {f.options?.map((o: string) => (
                <option key={o} value={o}>
                  {o === "true" ? "开启 (True)" : o === "false" ? "关闭 (False)" : o}
                </option>
              ))}
            </select>
            <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
          </div>
        ) : (
          <>
            <div className={f.key === "llm_model" ? "flex items-center gap-2" : ""}>
              <input
                type={f.type}
                value={values[f.key] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
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
              <div className="relative mt-2">
                <select
                  value={values[f.key] ?? ""}
                  onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                  className="w-full bg-white border border-slate-200 text-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 appearance-none cursor-pointer transition-all shadow-sm"
                >
                  <option value="">-- 请选择下拉模型 --</option>
                  {availableModels.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto animation-fade-in flex flex-col h-full relative">
      {/* 背景光晕 */}
      <div className="absolute top-[10%] left-[-10%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="mb-6 shrink-0 relative z-10">
        <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-400 tracking-tight pb-1">应用设置</h2>
        <p className="text-slate-500 mt-1 font-medium">全局配置参数，定制您的文件扫描和整理偏好。</p>
      </div>

      <div className="flex-1 overflow-y-auto pb-8 space-y-6 relative z-10">
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
                  配置 AI 不会处理的目录列表，每行一个或逗号分隔
                </p>
              </div>
              <div className="flex-1 max-w-md mt-1 sm:mt-0">
                <textarea
                  value={values.ai_exclude_paths || ""}
                  onChange={(e) => setValues((v) => ({ ...v, ai_exclude_paths: e.target.value }))}
                  placeholder={"例如：D:/Temp, D:/Downloads/Unsorted"}
                  rows={3}
                  className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400 shadow-sm resize-y"
                />
                <p className="mt-1.5 text-xs text-slate-500">
                  {values.ai_exclude_paths ? (
                    <span className="text-emerald-600 font-medium">
                      已配置 {values.ai_exclude_paths.split(/[,\n]/).filter(p => p.trim()).length} 个排除目录
                    </span>
                  ) : (
                    <span>未配置排除目录，AI 将处理所有文件</span>
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 p-8 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-800">AI 引擎配置</h3>
            {!isLoading && (
              <div className="flex items-center gap-2">
                <select
                  value={activeProfileId}
                  onChange={(e) => handleProfileChange(e.target.value)}
                  className="bg-slate-50 border border-slate-200 text-slate-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none cursor-pointer"
                >
                  {profiles.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.name || "未命名配置"}
                    </option>
                  ))}
                </select>
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
    </div>
  );
}
