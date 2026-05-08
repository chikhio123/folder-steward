# Frontend Heavy Pages Refactoring Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decouple and slim down the massive `SettingsPage.tsx` and `SuggestionPage.tsx` components by extracting UI components and custom hooks for state management.

**Architecture:** 
- Extract `PathTreeView` from `SettingsPage.tsx` into a reusable UI component.
- Extract complex `react-query` data fetching, mutations, and local state from `SettingsPage` into `useSettings.ts`.
- Extract complex `react-query` logic, pagination, filtering, and selection from `SuggestionPage` into `useSuggestions.ts`.

**Tech Stack:** React 19, Vite, TypeScript, React Query, Tailwind CSS

---

### Task 1: Extract PathTreeView Component

**Files:**
- Create: `D:\Code\Folder Steward\frontend\src\components\PathTreeView.tsx`
- Modify: `D:\Code\Folder Steward\frontend\src\pages\SettingsPage.tsx:18-128`

- [ ] **Step 1: Create PathTreeView component file**

```tsx
// D:\Code\Folder Steward\frontend\src\components\PathTreeView.tsx
import React, { useState } from 'react';
import { ChevronRight, ChevronDown, FolderOpen, X } from 'lucide-react';

export interface PathNode {
  name: string;
  path: string;
  children: Record<string, PathNode>;
  isTarget: boolean;
}

export function buildPathTree(paths: string[]): PathNode[] {
  const rootMap: Record<string, PathNode> = {};

  for (const p of paths) {
    const normalized = p.replace(/\\/g, '/');
    const parts = normalized.split('/').filter(Boolean);
    if (parts.length === 0) continue;

    const isUnix = normalized.startsWith('/');
    let currentMap = rootMap;
    let currentPath = isUnix ? '' : '';

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === 0 && isUnix) {
        currentPath = '/' + part;
      } else if (i === 0) {
        currentPath = part; // Windows drive e.g., C:
      } else {
        currentPath += '/' + part;
      }

      if (!currentMap[part]) {
        currentMap[part] = {
          name: part,
          path: currentPath,
          children: {},
          isTarget: false,
        };
      }

      if (i === parts.length - 1) {
        currentMap[part].isTarget = true;
      }

      currentMap = currentMap[part].children;
    }
  }

  return Object.values(rootMap).sort((a, b) => a.name.localeCompare(b.name));
}

export function PathTreeView({
  node,
  depth = 0,
  onRemove
}: {
  node: PathNode;
  depth?: number;
  onRemove: (path: string) => void
}) {
  const [expanded, setExpanded] = useState(true);
  const childNodes = Object.values(node.children).sort((a, b) => a.name.localeCompare(b.name));
  const hasChildren = childNodes.length > 0;

  return (
    <div className="flex flex-col">
      <div
        className="flex items-center group py-1.5 px-2 hover:bg-slate-100/50 rounded-lg transition-colors"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {hasChildren ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-5 h-5 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-200/50 rounded mr-1"
          >
            {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>
        ) : (
          <div className="w-5 h-5 mr-1" />
        )}

        <FolderOpen className="w-4 h-4 text-blue-400 mr-2 shrink-0" />

        <span className="font-mono text-sm text-slate-700 truncate" title={node.path}>
          {node.name}
        </span>

        {node.isTarget && (
          <>
            <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-emerald-50 text-emerald-600 border border-emerald-200/50 rounded">
              已排除
            </span>
            <button
              onClick={() => onRemove(node.path)}
              className="ml-auto p-1 text-slate-400 opacity-0 group-hover:opacity-100 hover:text-rose-500 hover:bg-rose-50 rounded transition-all"
              title="移除此排除目录"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </>
        )}
      </div>

      {expanded && hasChildren && (
        <div className="flex flex-col">
          {childNodes.map(child => (
            <PathTreeView key={child.path} node={child} depth={depth + 1} onRemove={onRemove} />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Update SettingsPage to import the new component**

Remove lines 18-128 (the `PathNode` interface, `buildPathTree` function, and `PathTreeView` component) from `SettingsPage.tsx`.

Add this import at the top of `D:\Code\Folder Steward\frontend\src\pages\SettingsPage.tsx`:
```typescript
import { PathTreeView, buildPathTree } from '../components/PathTreeView';
```

- [ ] **Step 3: Verify TypeScript builds**

Run: `tsc --noEmit` in frontend directory.
Expected: No errors related to `PathTreeView`.

- [ ] **Step 4: Commit**

```bash
git add src/components/PathTreeView.tsx src/pages/SettingsPage.tsx
git commit -m "refactor(frontend): extract PathTreeView component from SettingsPage"
```

### Task 2: Extract useSettings Hook

**Files:**
- Create: `D:\Code\Folder Steward\frontend\src\hooks\useSettings.ts`
- Modify: `D:\Code\Folder Steward\frontend\src\pages\SettingsPage.tsx`

- [ ] **Step 1: Create useSettings hook**

```typescript
// D:\Code\Folder Steward\frontend\src\hooks\useSettings.ts
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings, getAvailableModels } from '../services/api';
import toast from 'react-hot-toast';

interface ApiProfile {
  id: string;
  name: string;
  provider: string;
  api_key: string;
  base_url: string;
  model: string;
}

export const defaultSettings = {
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
          model: parsedData.llm_model || ""
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
        llm_model: activeProfile.model || ""
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
    mutationFn: () => {
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

  return {
    state: { values, profiles, activeProfileId, availableModels, isFetchingModels, showDeleteConfirm, isLoading },
    actions: { setValues, setProfiles, setActiveProfileId, setShowDeleteConfirm, fetchModels, updateMutation },
    utils: { getCurrentProfileUpdated }
  };
};
```

- [ ] **Step 2: Update SettingsPage to use the hook**

Edit `D:\Code\Folder Steward\frontend\src\pages\SettingsPage.tsx`:
1. Import the hook: `import { useSettings } from '../hooks/useSettings';`
2. Remove `ApiProfile` and `defaultSettings` interfaces/objects since they are now in the hook.
3. Replace all the state declarations and data fetching at the top of the component with:
```typescript
  const { state, actions, utils } = useSettings();
  const { values, profiles, activeProfileId, availableModels, isFetchingModels, showDeleteConfirm, isLoading } = state;
  const { setValues, setProfiles, setActiveProfileId, setShowDeleteConfirm, fetchModels, updateMutation } = actions;
  const { getCurrentProfileUpdated } = utils;
```

- [ ] **Step 3: Verify TypeScript builds**

Run: `tsc --noEmit` in frontend directory.
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add src/hooks/useSettings.ts src/pages/SettingsPage.tsx
git commit -m "refactor(frontend): extract useSettings hook from SettingsPage"
```

### Task 3: Extract useSuggestions Hook

**Files:**
- Create: `D:\Code\Folder Steward\frontend\src\hooks\useSuggestions.ts`
- Modify: `D:\Code\Folder Steward\frontend\src\pages\SuggestionPage.tsx`

- [ ] **Step 1: Create useSuggestions hook**

```typescript
// D:\Code\Folder Steward\frontend\src\hooks\useSuggestions.ts
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSuggestions, generateSuggestions, updateSuggestion, executeSuggestions, bulkRejectSuggestions } from '../services/api';
import toast from 'react-hot-toast';

export const useSuggestions = () => {
  const queryClient = useQueryClient();
  const [archiveRoot, setArchiveRoot] = useState(() => localStorage.getItem("fs_last_archive_root") || "D:/Archive");
  const [filter, setFilter] = useState("pending");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editPath, setEditPath] = useState("");
  const [showConfirmCancel, setShowConfirmCancel] = useState(false);

  useEffect(() => {
    if (archiveRoot.trim()) {
      localStorage.setItem("fs_last_archive_root", archiveRoot.trim());
    }
  }, [archiveRoot]);

  const { data, isLoading } = useQuery({
    queryKey: ["suggestions", filter, page],
    queryFn: () => getSuggestions({ status: filter === "all" ? undefined : filter, page, page_size: 50 }),
  });

  const generateMutation = useMutation({
    mutationFn: () => generateSuggestions(archiveRoot),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setPage(1);
      setFilter("pending");
      toast.success(`成功生成 ${data.created_count} 条建议`);
    },
    onError: (err: any) => toast.error(`生成失败: ${err.message}`),
  });

  const acceptMutation = useMutation({
    mutationFn: (id: number) => updateSuggestion(id, { status: "accepted" }),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setSelected((prev) => new Set(prev).add(id));
      toast.success("已同意并选中");
    },
    onError: (err: any) => toast.error(`操作失败: ${err.message}`),
  });

  const rejectOneMutation = useMutation({
    mutationFn: (id: number) => updateSuggestion(id, { status: "rejected" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      toast.success("已拒绝该建议");
    },
    onError: (err: any) => toast.error(`拒绝失败: ${err.message}`),
  });

  const savePathMutation = useMutation({
    mutationFn: ({ id, path }: { id: number, path: string }) => updateSuggestion(id, { target_path: path }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setEditingId(null);
      toast.success("目标路径已更新");
    },
    onError: (err: any) => {
      toast.error(`保存失败: ${err.message}`);
    }
  });

  const executeMutation = useMutation({
    mutationFn: () => executeSuggestions(Array.from(selected)),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setSelected(new Set());
      if (data.failed_count > 0) {
        toast.error(`${data.success_count} 个成功，${data.failed_count} 个失败`);
      } else {
        toast.success(`成功执行 ${data.success_count} 条操作`);
      }
    },
    onError: (err: any) => toast.error(`执行出错: ${err.message}`),
  });

  const bulkRejectMutation = useMutation({
    mutationFn: () => bulkRejectSuggestions(filter === "all" ? "pending" : filter),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setSelected(new Set());
      setPage(1);
      setShowConfirmCancel(false);
      toast.success(`已取消 ${data.rejected_count} 条建议`);
    },
    onError: (err: any) => {
      setShowConfirmCancel(false);
      toast.error(`取消失败: ${err.message}`);
    },
  });

  return {
    state: { archiveRoot, filter, page, selected, editingId, editPath, showConfirmCancel, data, isLoading },
    actions: { setArchiveRoot, setFilter, setPage, setSelected, setEditingId, setEditPath, setShowConfirmCancel },
    mutations: { generateMutation, acceptMutation, rejectOneMutation, savePathMutation, executeMutation, bulkRejectMutation }
  };
};
```

- [ ] **Step 2: Update SuggestionPage to use the hook**

Edit `D:\Code\Folder Steward\frontend\src\pages\SuggestionPage.tsx`:
1. Import the hook: `import { useSuggestions } from '../hooks/useSuggestions';`
2. Replace all the state declarations and mutations at the top of the component with:
```typescript
  const { state, actions, mutations } = useSuggestions();
  const { archiveRoot, filter, page, selected, editingId, editPath, showConfirmCancel, data, isLoading } = state;
  const { setArchiveRoot, setFilter, setPage, setSelected, setEditingId, setEditPath, setShowConfirmCancel } = actions;
  const { generateMutation, acceptMutation, rejectOneMutation, savePathMutation, executeMutation, bulkRejectMutation } = mutations;
```

- [ ] **Step 3: Verify TypeScript builds**

Run: `tsc --noEmit` in frontend directory.
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add src/hooks/useSuggestions.ts src/pages/SuggestionPage.tsx
git commit -m "refactor(frontend): extract useSuggestions hook from SuggestionPage"
```