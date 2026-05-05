import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSettings, updateSettings } from "../services/api";
import { useState, useEffect } from "react";
import { Settings, Save, Loader2, FolderArchive, ShieldAlert, FileDigit, EyeOff } from "lucide-react";
import { twMerge } from "tailwind-merge";
import toast from "react-hot-toast";

const defaultSettings = {
  archive_root: "",
  scan_hidden_files: "false",
  max_file_size_for_hash: "104857600",
  skip_system_directories: "true",
};

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const [values, setValues] = useState<Record<string, string>>(defaultSettings);

  useEffect(() => {
    if (data) setValues({ ...defaultSettings, ...data });
  }, [data]);

  const updateMutation = useMutation({
    mutationFn: () => updateSettings(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("全局设置已成功保存！");
    },
    onError: (err) => {
      toast.error(`保存设置失败: ${err.message}`);
    }
  });

  const fields = [
    { key: "archive_root", label: "默认归档目录", desc: "整理建议生成的默认目标文件夹路径", type: "text", placeholder: "例如：D:/Archive", icon: FolderArchive },
    { key: "scan_hidden_files", label: "扫描隐藏文件", desc: "是否将以点 (.) 开头的隐藏文件纳入索引", type: "select", options: ["true", "false"], icon: EyeOff },
    { key: "max_file_size_for_hash", label: "Hash 计算上限 (字节)", desc: "超过此大小的文件将跳过 SHA-256 哈希计算以节省时间", type: "number", icon: FileDigit },
    { key: "skip_system_directories", label: "跳过系统目录", desc: "自动跳过 Windows/System32 等敏感目录以保护系统安全", type: "select", options: ["true", "false"], icon: ShieldAlert },
  ];

  return (
    <div className="max-w-4xl mx-auto animation-fade-in flex flex-col h-full">
      <div className="mb-6 shrink-0">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">应用设置</h2>
        <p className="text-slate-500 mt-1">全局配置参数，定制您的文件扫描和整理偏好。</p>
      </div>

      <div className="flex-1 overflow-y-auto pb-8">
        <div className="bg-white rounded-2xl border border-slate-200/60 p-8 shadow-sm">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center text-slate-400 py-10 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p>加载设置中...</p>
            </div>
          ) : (
            <div className="space-y-8">
              {fields.map((f) => (
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
                          {f.options?.map((o) => (
                            <option key={o} value={o}>{o === "true" ? "开启 (True)" : "关闭 (False)"}</option>
                          ))}
                        </select>
                        <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                          <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                      </div>
                    ) : (
                      <input
                        type={f.type}
                        value={values[f.key] ?? ""}
                        onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                        placeholder={f.placeholder}
                        className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400 shadow-sm"
                      />
                    )}
                  </div>
                </div>
              ))}

              <div className="pt-4 flex justify-end">
                <button
                  onClick={() => updateMutation.mutate()}
                  disabled={updateMutation.isPending}
                  className="px-6 py-3 bg-blue-600 text-white rounded-xl text-sm font-semibold shadow-sm shadow-blue-600/20 hover:bg-blue-700 hover:shadow-md active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-2"
                >
                  {updateMutation.isPending ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> 保存中</>
                  ) : (
                    <><Save className="w-4 h-4" /> 保存全局设置</>
                  )}
                </button>
              </div>

              {updateMutation.isSuccess && (
                <div className="text-right text-emerald-600 text-sm font-medium mt-2 flex items-center justify-end gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                  设置已成功保存并生效
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
