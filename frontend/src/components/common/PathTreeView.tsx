import { useState } from 'react';
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