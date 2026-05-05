import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../services/api";

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
    refetchInterval: 10_000,
  });

  if (isLoading) {
    return <div className="text-gray-500">加载中...</div>;
  }

  const stats = [
    { label: "已索引文件", value: data?.total_files ?? 0 },
    { label: "总文件大小", value: formatSize(data?.total_size ?? 0) },
    { label: "重复文件组", value: data?.duplicate_groups ?? 0 },
    { label: "待处理建议", value: data?.pending_suggestions ?? 0 },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">概览</h2>
      <div className="grid grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-500">{s.label}</div>
            <div className="text-2xl font-semibold text-gray-800 mt-1">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-medium text-gray-800 mb-3">最近扫描任务</h3>
          {data?.recent_tasks?.length ? (
            <div className="space-y-2">
              {data.recent_tasks.map((t) => (
                <div key={t.task_id} className="bg-white border border-gray-200 rounded-lg p-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 truncate">{t.root_path}</span>
                    <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${statusColor(t.status)}`}>
                      {t.status}
                    </span>
                  </div>
                  <div className="text-gray-400 text-xs mt-1">
                    {t.scanned_files}/{t.total_files} 文件
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">暂无扫描记录</p>
          )}
        </div>

        <div>
          <h3 className="text-lg font-medium text-gray-800 mb-3">最近操作</h3>
          {data?.recent_operations?.length ? (
            <div className="space-y-2">
              {data.recent_operations.map((o) => (
                <div key={o.id} className="bg-white border border-gray-200 rounded-lg p-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 truncate">{o.source_path}</span>
                    <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${statusColor(o.status)}`}>
                      {o.status}
                    </span>
                  </div>
                  <div className="text-gray-400 text-xs mt-1">{o.operation_type}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">暂无操作记录</p>
          )}
        </div>
      </div>
    </div>
  );
}

function formatSize(bytes: number): string {
  if (bytes >= 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(1)} GB`;
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(1)} KB`;
  return `${bytes} B`;
}

function statusColor(status: string): string {
  switch (status) {
    case "completed":
    case "success":
      return "bg-green-100 text-green-700";
    case "running":
      return "bg-blue-100 text-blue-700";
    case "failed":
      return "bg-red-100 text-red-700";
    case "cancelled":
      return "bg-yellow-100 text-yellow-700";
    default:
      return "bg-gray-100 text-gray-600";
  }
}
