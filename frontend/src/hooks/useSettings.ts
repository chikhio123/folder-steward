import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings, getAvailableModels } from '../services/api';
import toast from 'react-hot-toast';

export interface ApiProfile {
  id: string;
  name: string;
  provider: string;
  api_key: string;
  base_url: string;
  model: string;
}

export const defaultSettings: Record<string, string> = {
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

export const useSettings = () => {
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
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

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

      const activeProfile = loadedProfiles.find((p: ApiProfile) => p.id === activeId) || loadedProfiles[0];
      setValues({
        ...parsedData,
        llm_profile_name: activeProfile.name || "",
        llm_provider: activeProfile.provider || "mock",
        llm_api_key: activeProfile.api_key || "",
        llm_base_url: activeProfile.base_url || "",
        llm_model: activeProfile.model || "gpt-4o-mini"
      });
    }
  }, [data]);

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

  const getCurrentProfileUpdated = () => ({
    provider: values.llm_provider,
    api_key: values.llm_api_key,
    base_url: values.llm_base_url,
    model: values.llm_model,
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      const finalProfiles = profiles.map((p: ApiProfile) =>
        p.id === activeProfileId ? { ...p, ...getCurrentProfileUpdated(), name: values.llm_profile_name || p.name } : p
      );

      const payload: Record<string, string> = {
        ...values,
        llm_profiles: JSON.stringify(finalProfiles),
        active_llm_profile_id: activeProfileId
      };

      let parsedAiPaths: string[] = [];
      if (values.ai_exclude_paths) {
        parsedAiPaths = values.ai_exclude_paths
          .split(/[,\n]/)
          .map((p: string) => p.trim())
          .filter((p: string) => p);
        payload.ai_exclude_paths = JSON.stringify(parsedAiPaths);
      } else {
        payload.ai_exclude_paths = "[]";
      }

      delete payload.llm_profile_name;

      return updateSettings(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("全局设置已成功保存！");
    },
    onError: (err: any) => {
      toast.error(`保存设置失败: ${err.message}`);
    }
  });

  const handleRemoveExcludePath = (pathToRemove: string) => {
    const paths = (values.ai_exclude_paths || "").split("\n").filter((p: string) => p.trim() && p !== pathToRemove);
    setValues((v: Record<string, string>) => ({ ...v, ai_exclude_paths: paths.join("\n") }));
  };

  const handleAddExcludePath = async () => {
    // @ts-ignore
    if (window.electronAPI?.selectDirectory) {
      // @ts-ignore
      const dirPath = await window.electronAPI.selectDirectory();
      if (dirPath) {
        const currentPaths = (values.ai_exclude_paths || "").split("\n").map((p: string) => p.trim()).filter((p: string) => p);
        if (!currentPaths.includes(dirPath)) {
          currentPaths.push(dirPath);
          setValues((v: Record<string, string>) => ({ ...v, ai_exclude_paths: currentPaths.join("\n") }));
        }
      }
    } else {
      const dirPath = window.prompt("请输入要排除的目录完整路径：");
      if (dirPath && dirPath.trim()) {
        const currentPaths = (values.ai_exclude_paths || "").split("\n").map((p: string) => p.trim()).filter((p: string) => p);
        if (!currentPaths.includes(dirPath.trim())) {
          currentPaths.push(dirPath.trim());
          setValues((v: Record<string, string>) => ({ ...v, ai_exclude_paths: currentPaths.join("\n") }));
        }
      }
    }
  };

  const handleProfileChange = (id: string) => {
    // Save current values to old profile
    const updatedProfiles = profiles.map((p: ApiProfile) =>
      p.id === activeProfileId ? { ...p, ...getCurrentProfileUpdated(), name: values.llm_profile_name || p.name } : p
    );
    setProfiles(updatedProfiles);
    setActiveProfileId(id);

    // Load new profile into values
    const newProfile = updatedProfiles.find((p: ApiProfile) => p.id === id);
    if (newProfile) {
      setValues((v: Record<string, string>) => ({
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
    const updatedProfiles = [...profiles.map((p: ApiProfile) =>
      p.id === activeProfileId ? { ...p, ...getCurrentProfileUpdated(), name: values.llm_profile_name || p.name } : p
    ), newProfile];
    
    setProfiles(updatedProfiles);
    setActiveProfileId(newId);
    setValues((v: Record<string, string>) => ({
      ...v,
      llm_profile_name: newProfile.name,
      llm_provider: newProfile.provider,
      llm_api_key: newProfile.api_key,
      llm_base_url: newProfile.base_url,
      llm_model: newProfile.model
    }));
  };

  const handleDeleteProfile = () => {
    if (profiles.length <= 1) {
      toast.error("必须保留至少一个配置");
      return;
    }
    setShowDeleteConfirm(true);
  };

  const confirmDeleteProfile = () => {
    const remaining = profiles.filter((p: ApiProfile) => p.id !== activeProfileId);
    setProfiles(remaining);
    setActiveProfileId(remaining[0].id);
    setValues((v: Record<string, string>) => ({
      ...v,
      llm_profile_name: remaining[0].name,
      llm_provider: remaining[0].provider,
      llm_api_key: remaining[0].api_key,
      llm_base_url: remaining[0].base_url,
      llm_model: remaining[0].model
    }));
    setShowDeleteConfirm(false);
  };

  return {
    state: { values, profiles, activeProfileId, availableModels, isFetchingModels, showDeleteConfirm, isLoading },
    actions: { 
      setValues, 
      setProfiles, 
      setActiveProfileId, 
      setShowDeleteConfirm, 
      fetchModels, 
      updateMutation,
      handleRemoveExcludePath,
      handleAddExcludePath,
      handleProfileChange,
      handleAddProfile,
      handleDeleteProfile,
      confirmDeleteProfile
    },
    utils: { getCurrentProfileUpdated }
  };
};