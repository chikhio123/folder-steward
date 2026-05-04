import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getOperations, rollbackOperation } from "../services/api";
import type { OperationLog } from "../types";

export default function OperationHistoryPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["operations", page],
    queryFn: () => getOperations({ page, page_size: 50 }),
  });

  const rollbackMutation = useMutation({
    mutationFn: (id: number) => rollbackOperation(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["operations"] }),
  });

  const totalPages = data ? Math.ceil(data.total / 50) : 1;

  if (isLoading) {
    return <div className="text-gray-500">加载中...</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">操作历史</h2>

      {data?.items?.length ? (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-gray-600 font-medium">类型</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">源路径</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">目标路径</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">状态</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">执行时间</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((o: OperationLog) => (
                <tr key={o.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-700">{o.operation_type}</td>
                  <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{o.source_path}</td>
                  <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{o.target_path ?? "-"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusBadge(o.status)}`}>
                      {o.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {o.executed_at ? o.executed_at.slice(0, 19) : "-"}
                  </td>
                  <td className="px-4 py-3">
                    {o.rollback_available && o.status === "success" ? (
                      <button
                        onClick={() => rollbackMutation.mutate(o.id)}
                        disabled={rollbackMutation.isPending}
                        className="text-xs px-3 py-1 bg-yellow-100 text-yellow-700 rounded-md hover:bg-yellow-200 disabled:opacity-50"
                      >
                        撤销
                      </button>
                    ) : (
                      <span className="text-xs text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">
          暂无操作记录
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
    case "success": return "bg-green-100 text-green-700";
    case "failed": return "bg-red-100 text-red-700";
    case "rolled_back": return "bg-yellow-100 text-yellow-700";
    default: return "bg-gray-100 text-gray-600";
  }
}
