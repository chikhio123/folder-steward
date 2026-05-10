import { useState, useMemo, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getExcludePaths, updateExcludePaths } from "../services/api";
import { X, Search, ShieldAlert, Loader2, FolderMinus, ChevronRight, ChevronDown } from "lucide-react";
import toast from "react-hot-toast";
import { twMerge } from "tailwind-merge";
import type { OrganizePlanItem } from "../types";

function normalizePath(p: string): string {
  return p.replace(/\\/g, '/');
}

function isRootPath(path: string): boolean {
  const p = normalizePath(path);
  return p === "/" || /^[A-Za-z]:\/?$/.test(p);
}

function isSameOrDescendant(path: string, ancestor: string): boolean {
  const p = normalizePath(path).toLowerCase();
  const a = normalizePath(ancestor).toLowerCase().replace(/\/+$/, "");
  return p === a || p.startsWith(a + "/");
}

function simplifyPaths(paths: string[]): string[] {
  const sorted = [...paths].map(normalizePath).sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
  const result: string[] = [];
  for (const p of sorted) {
    if (result.length === 0 || !isSameOrDescendant(p, result[result.length - 1])) {
      result.push(p);
    }
  }
  return result;
}

function getAllAncestors(path: string): string[] {
  const p = normalizePath(path);
  const parts = p.split('/');
  const ancestors: string[] = [];

  if (p.startsWith('/')) { // Unix
    ancestors.push("/");
    let cur = "";
    for (let i = 1; i < parts.length; i++) {
      if (parts[i]) {
        cur += "/" + parts[i];
        ancestors.push(cur);
      }
    }
  } else { // Windows
    let cur = parts[0];
    ancestors.push(cur + "/");
    for (let i = 1; i < parts.length; i++) {
      if (parts[i]) {
        cur += "/" + parts[i];
        ancestors.push(cur);
      }
    }
  }
  return ancestors;
}

interface TreeNodeData {
  path: string;
  name: string;
  children: Record<string, TreeNodeData>;
  isPlanDir: boolean;
}

function buildTree(paths: string[]): TreeNodeData[] {
  const nodeMap: Record<string, TreeNodeData> = {};
  const roots: TreeNodeData[] = [];

  for (const path of paths) {
    const ancestors = getAllAncestors(path);
    for (let i = 0; i < ancestors.length; i++) {
      const anc = ancestors[i];
      if (!nodeMap[anc]) {
        const name = i === 0 ? anc : anc.split('/').pop() || anc;
        nodeMap[anc] = { path: anc, name, children: {}, isPlanDir: false };

        if (i === 0) {
          roots.push(nodeMap[anc]);
        } else {
          const parent = ancestors[i - 1];
          if (nodeMap[parent]) {
            nodeMap[parent].children[anc] = nodeMap[anc];
          }
        }
      }
      if (anc === normalizePath(path)) {
        nodeMap[anc].isPlanDir = true;
      }
    }
  }
  return roots;
}

function getNodeState(path: string, existingExcluded: string[], selectedDirs: Set<string>) {
  const isExistingExcluded = existingExcluded.some(ex => isSameOrDescendant(path, ex));
  const normPathLower = normalizePath(path).toLowerCase();

  if (isExistingExcluded) {
    const isDirect = existingExcluded.some(ex => normalizePath(ex).toLowerCase() === normPathLower);
    return { checked: true, indeterminate: false, disabled: true, isDirect };
  }

  const isSelected = Array.from(selectedDirs).some(sel => isSameOrDescendant(path, sel));
  if (isSelected) {
    const isDirect = Array.from(selectedDirs).some(sel => normalizePath(sel).toLowerCase() === normPathLower);
    return { checked: true, indeterminate: false, disabled: !isDirect, isDirect };
  }

  const hasExcludedDescendant = existingExcluded.some(ex => isSameOrDescendant(ex, path));
  const hasSelectedDescendant = Array.from(selectedDirs).some(sel => isSameOrDescendant(sel, path));

  if (hasExcludedDescendant || hasSelectedDescendant) {
    return { checked: false, indeterminate: true, disabled: false, isDirect: false };
  }

  return { checked: false, indeterminate: false, disabled: false, isDirect: false };
}

interface TriStateCheckboxProps {
  checked: boolean;
  indeterminate: boolean;
  disabled?: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

function TriStateCheckbox({ checked, indeterminate, disabled, onChange }: TriStateCheckboxProps) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (ref.current) {
      ref.current.indeterminate = indeterminate && !checked;
    }
  }, [checked, indeterminate]);

  return (
    <input
      type="checkbox"
      ref={ref}
      checked={checked}
      disabled={disabled}
      onChange={onChange}
      className={twMerge(
        "w-4 h-4 rounded border-slate-300 focus:ring-blue-500 cursor-pointer transition-all",
        disabled ? "opacity-50 cursor-not-allowed bg-slate-100" : "text-blue-600"
      )}
    />
  );
}

interface ExcludeDirsModalProps {
  isOpen: boolean;
  onClose: () => void;
  planGroups?: Record<string, OrganizePlanItem[]>;
}

export function ExcludeDirsModal({ isOpen, onClose, planGroups }: ExcludeDirsModalProps) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [selectedDirs, setSelectedDirs] = useState<Set<string>>(new Set());
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!isOpen) {
      setSelectedDirs(new Set());
      setSearch("");
      setExpandedNodes(new Set());
    }
  }, [isOpen]);

  const { data: excludeData, isLoading } = useQuery({
    queryKey: ["exclude-paths"],
    queryFn: getExcludePaths,
    enabled: isOpen,
  });

  const existingExcluded = useMemo(() => (excludeData?.exclude_paths || []).map(normalizePath), [excludeData]);

  const updateMutation = useMutation({
    mutationFn: updateExcludePaths,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exclude-paths"] });
      toast.success(`已更新排除目录配置，建议重新生成 Plan`);
      setSelectedDirs(new Set());
      onClose();
    },
    onError: (err: Error) => {
      toast.error(`更新排除列表失败: ${err.message}`);
    }
  });

  const removeMutation = useMutation({
    mutationFn: (newPaths: string[]) => updateExcludePaths(newPaths),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exclude-paths"] });
      toast.success("已移除排除规则");
    },
    onError: (err: Error) => {
      toast.error(`更新排除列表失败: ${err.message}`);
    }
  });

  const rootNodes = useMemo(() => {
    if (!planGroups) return [];
    const sourcePaths = new Set<string>();
    Object.values(planGroups).flat().forEach(item => {
      const src = item.source_path as string;
      if (src) {
        const parent = normalizePath(src).replace(/\/[^/]+$/, '');
        if (parent) {
          sourcePaths.add(parent);
        }
      }
    });
    return buildTree(Array.from(sourcePaths));
  }, [planGroups]);

  const { visibleNodes, matchPaths } = useMemo(() => {
    if (!search) return { visibleNodes: rootNodes, matchPaths: new Set<string>() };

    const mPaths = new Set<string>();
    const lowerSearch = search.toLowerCase();

    function traverse(n: TreeNodeData): boolean {
      const isMatch = n.name.toLowerCase().includes(lowerSearch) || n.path.toLowerCase().includes(lowerSearch);
      let hasVisibleChild = false;
      for (const child of Object.values(n.children)) {
        if (traverse(child)) hasVisibleChild = true;
      }
      if (isMatch || hasVisibleChild) {
        mPaths.add(n.path);
        return true;
      }
      return false;
    }

    const vNodes = rootNodes.filter(traverse);
    return { visibleNodes: vNodes, matchPaths: mPaths };
  }, [rootNodes, search]);

  useEffect(() => {
    if (isOpen && search && matchPaths.size > 0) {
      setExpandedNodes(prev => new Set([...prev, ...matchPaths]));
    }
  }, [isOpen, search, matchPaths]);

  const toggleExpand = (path: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const handleCheckboxChange = (node: TreeNodeData, state: ReturnType<typeof getNodeState>) => {
    const isRoot = isRootPath(node.path);
    if (isRoot || state.disabled) return;

    const next = new Set(selectedDirs);
    const p = normalizePath(node.path);

    if (state.checked) {
      // Uncheck
      next.delete(p);
    } else {
      // Check
      for (const sel of next) {
        if (isSameOrDescendant(sel, p)) {
          next.delete(sel);
        }
      }
      next.add(p);
    }
    setSelectedDirs(next);
  };

  const handleRemoveExcluded = (dir: string) => {
    const nextPaths = existingExcluded.filter(p => p !== dir);
    removeMutation.mutate(nextPaths);
  };

  const handleSubmit = () => {
    if (selectedDirs.size === 0) {
      toast("未选择新的排除目录");
      return;
    }
    const combined = simplifyPaths([...existingExcluded, ...Array.from(selectedDirs)]);
    updateMutation.mutate(combined);
  };

  const renderNode = (node: TreeNodeData, depth: number) => {
    if (search && !matchPaths.has(node.path)) return null;

    const isExpanded = expandedNodes.has(node.path);
    const children = Object.values(node.children).sort((a, b) => a.name.localeCompare(b.name));
    const hasChildren = children.length > 0;

    const state = getNodeState(node.path, existingExcluded, selectedDirs);
    const isRoot = isRootPath(node.path);
    const disableCheckbox = state.disabled || isRoot;

    return (
      <div key={node.path}>
        <div className="flex items-center py-1.5 hover:bg-slate-50 transition-colors group">
          <div style={{ width: `${depth * 20}px` }} className="shrink-0" />

          <button
            onClick={() => hasChildren && toggleExpand(node.path)}
            className={twMerge(
              "p-0.5 rounded text-slate-400 hover:bg-slate-200 hover:text-slate-600 transition-colors mr-1 shrink-0",
              !hasChildren && "invisible"
            )}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>

          <div
            className="flex items-center gap-2 min-w-0 flex-1 cursor-pointer"
            onClick={() => !disableCheckbox && handleCheckboxChange(node, state)}
          >
            <TriStateCheckbox
              checked={state.checked}
              indeterminate={state.indeterminate}
              disabled={disableCheckbox}
              onChange={() => {}}
            />
            <span
              className={twMerge(
                "text-sm font-mono truncate select-none",
                state.checked ? "text-slate-500" : "text-slate-700"
              )}
              title={isRoot ? "为防止误伤，根目录禁止整体排除" : node.path}
            >
              {node.name}
            </span>
            {isRoot && (
              <span className="shrink-0 text-[10px] px-1.5 py-0.5 bg-rose-50 text-rose-600 rounded border border-rose-200 font-medium">
                ROOT
              </span>
            )}
            {state.checked && state.isDirect && existingExcluded.includes(normalizePath(node.path)) && (
              <span className="shrink-0 text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded border border-slate-200 font-medium">
                已排除
              </span>
            )}
          </div>
        </div>

        {isExpanded && hasChildren && (
          <div>
            {children.map(c => renderNode(c, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animation-fade-in">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden border border-slate-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2 text-slate-800">
            <ShieldAlert className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-bold">管理 AI 排除目录</h2>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col sm:flex-row divide-y sm:divide-y-0 sm:divide-x divide-slate-100">

          {/* Left panel: Available Dirs from Plan (Tree) */}
          <div className="flex-1 flex flex-col min-h-0 sm:w-2/3">
            <div className="px-6 py-4 flex flex-col gap-3 border-b border-slate-100 shrink-0">
              <h3 className="text-sm font-semibold text-slate-700">可排除的目录 (来自当前 Plan)</h3>
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="搜索目录路径..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 text-slate-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all shadow-sm"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 bg-white">
              {rootNodes.length === 0 ? (
                <div className="flex-1 flex items-center justify-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-200 h-full">
                  <p className="text-sm text-slate-500">当前没有待整理的目录</p>
                </div>
              ) : (
                <div className="space-y-0.5">
                  {visibleNodes.map(node => renderNode(node, 0))}
                  {visibleNodes.length === 0 && (
                    <div className="p-8 text-center text-sm text-slate-500 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                      没有匹配的目录
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right panel: Currently Excluded */}
          <div className="flex-1 flex flex-col min-h-0 sm:w-1/3 bg-slate-50/50">
            <div className="px-6 py-4 border-b border-slate-100 shrink-0">
              <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <FolderMinus className="w-4 h-4 text-slate-400" />
                已排除列表 ({existingExcluded.length})
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {isLoading ? (
                <div className="text-sm text-slate-500 py-4 text-center"><Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-500" />加载中...</div>
              ) : existingExcluded.length === 0 ? (
                <div className="text-sm text-slate-500 py-6 px-4 text-center">
                  暂无全局排除目录
                </div>
              ) : (
                <div className="space-y-1">
                  {existingExcluded.map(dir => (
                    <div key={dir} className="flex items-center justify-between px-3 py-2 bg-white rounded-lg border border-slate-200 shadow-sm hover:border-slate-300 transition-colors group">
                      <span className="text-xs text-slate-600 font-mono truncate mr-2" title={dir}>
                        {dir.split('/').pop() || dir}
                      </span>
                      <button
                        onClick={() => handleRemoveExcluded(dir)}
                        disabled={removeMutation.isPending}
                        className="text-slate-400 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-all p-1 bg-rose-50 hover:bg-rose-100 rounded"
                        title={`取消排除: ${dir}`}
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>

        <div className="flex items-center justify-between px-6 py-4 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgb(0,0,0,0.05)]">
          <div className="text-sm text-slate-500">
            {selectedDirs.size > 0 ? (
              <span>已选 <span className="font-semibold text-blue-600">{selectedDirs.size}</span> 项待添加到全局排除</span>
            ) : null}
          </div>
          <div className="flex gap-3">
            <button onClick={onClose} className="px-5 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors">
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={selectedDirs.size === 0 || updateMutation.isPending}
              className="px-6 py-2.5 flex items-center gap-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-all disabled:opacity-50 disabled:pointer-events-none shadow-sm shadow-blue-600/20"
            >
              {updateMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              保存并应用
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
