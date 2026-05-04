import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSuggestions, generateSuggestions, updateSuggestion, executeSuggestions } from "../services/api";
import type { FileSuggestion } from "../types";

export default function SuggestionPage() {
  const queryClient = useQueryClient();
  const [archiveRoot, setArchiveRoot] = useState("D:/Archive");
  const [filter, setFilter] = useState("pending");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const { data, isLoading } = useQuery({
    queryKey: ["suggestions", filter, page],
    queryFn: () => getSuggestions({ status: filter, page, page_size: 50 }),
  });

  const generateMutation = useMutation({
    mutationFn: () => generateSuggestions(archiveRoot),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["suggestions"] }),
  });

  const acceptMutation = useMutation({
    mutationFn: (id: number) => updateSuggestion(id, { status: "accepted" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["suggestions"] }),
  });

  const executeMutation = useMutation({
    mutationFn: () => executeSuggestions(Array.from(selected)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setSelected(new Set());
    },
  });

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const totalPages = data ? Math.ceil(data.total / 50) : 1;

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">整理建议</h2>

      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4 flex gap-3 items-center flex-wrap">
        <input
          type="text"
          value={archiveRoot}
          onChange={(e) => setArchiveRoot(e.target.value)}
          placeholder="归档根目录"
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm flex-1 min-w-[200px] focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="px-4 py-1.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {generateMutation.isPending ? "生成中..." : "生成整理建议"}
        </button>
      </div>

      <div className="mb-4 flex gap-2 items-center">
        <select
          value={filter}
          onChange={(e) => { setFilter(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm"
        >
          <option value="pending">待处理</option>
          <option value="accepted">已接受</option>
          <option value="rejected">已拒绝</option>
          <option value="">全部</option>
        </select>
        {selected.size > 0 && (
          <button
            onClick={() => executeMutation.mutate()}
            disabled={executeMutation.isPending}
            className="px-4 py-1.5 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 disabled:opacity-50"
          >
            执行已选 ({selected.size})
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="text-gray-500">加载中...</div>
      ) : data?.items?.length ? (
        <div className="space-y-2">
          {data.items.map((s: FileSuggestion) => (
            <div
              key={s.id}
              className={`bg-white rounded-lg border p-4 ${selected.has(s.id) ? "border-blue-400 ring-2 ring-blue-100" : "border-gray-200"}`}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={selected.has(s.id)}
                  onChange={() => toggle(s.id)}
                  disabled={s.status !== "pending"}
                  className="mt-1"
                />
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-gray-800 truncate">{s.source_path}</div>
                  <div className="text-sm text-blue-600 truncate mt-1">→ {s.target_path}</div>
                  {s.reason && <div className="text-xs text-gray-500 mt-1">{s.reason}</div>}
                  <div className="flex gap-2 mt-2">
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">{s.suggestion_type}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">{(s.confidence * 100).toFixed(0)}%</span>
                    {s.conflict_status !== "none" && (
                      <span className="text-xs px-2 py-0.5 rounded bg-yellow-100 text-yellow-700">{s.conflict_status}</span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  {s.status === "pending" && (
                    <>
                      <button
                        onClick={() => acceptMutation.mutate(s.id)}
                        className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded-md hover:bg-green-200"
                      >
                        接受
                      </button>
                      <button
                        onClick={() => updateSuggestion(s.id, { status: "rejected" }).then(() => queryClient.invalidateQueries({ queryKey: ["suggestions"] }))}
                        className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200"
                      >
                        拒绝
                      </button>
                    </>
                  )}
                  <span className={`px-2 py-1 text-xs rounded ${statusBadge(s.status)}`}>
                    {s.status}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">
          暂无整理建议
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-40"
          >
            上一页
          </button>
          <span className="px-3 py-1 text-sm text-gray-500">{page} / {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-40"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}

function statusBadge(status: string): string {
  switch (status) {
    case "pending": return "bg-yellow-100 text-yellow-700";
    case "accepted": return "bg-blue-100 text-blue-700";
    case "rejected": return "bg-gray-100 text-gray-500";
    case "executed": return "bg-green-100 text-green-700";
    case "failed": return "bg-red-100 text-red-700";
    default: return "bg-gray-100 text-gray-600";
  }
}
