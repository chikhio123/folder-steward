import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSettings, updateSettings } from "../services/api";
import { useState, useEffect } from "react";

const defaultSettings = {
  archive_root: "",
  scan_hidden_files: "false",
  max_file_size_for_hash: "104857600",
  skip_system_directories: "true",
};

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const [values, setValues] = useState<Record<string, string>>(defaultSettings);

  useEffect(() => {
    if (data) setValues({ ...defaultSettings, ...data });
  }, [data]);

  const updateMutation = useMutation({
    mutationFn: () => updateSettings(values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["settings"] }),
  });

  const fields = [
    { key: "archive_root", label: "默认归档目录", type: "text", placeholder: "D:/Archive" },
    { key: "scan_hidden_files", label: "扫描隐藏文件", type: "select", options: ["true", "false"] },
    { key: "max_file_size_for_hash", label: "Hash 计算最大文件大小 (字节)", type: "number" },
    { key: "skip_system_directories", label: "跳过系统目录", type: "select", options: ["true", "false"] },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">设置</h2>

      <div className="bg-white rounded-lg border border-gray-200 p-6 max-w-xl">
        <div className="space-y-4">
          {fields.map((f) => (
            <div key={f.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{f.label}</label>
              {f.type === "select" ? (
                <select
                  value={values[f.key] ?? ""}
                  onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {f.options?.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              ) : (
                <input
                  type={f.type}
                  value={values[f.key] ?? ""}
                  onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                  placeholder={f.placeholder}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              )}
            </div>
          ))}
        </div>

        <button
          onClick={() => updateMutation.mutate()}
          disabled={updateMutation.isPending}
          className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {updateMutation.isPending ? "保存中..." : "保存设置"}
        </button>
      </div>
    </div>
  );
}
