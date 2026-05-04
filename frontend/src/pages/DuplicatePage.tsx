import { useQuery } from "@tanstack/react-query";
import { getDuplicates } from "../services/api";

export default function DuplicatePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["duplicates"],
    queryFn: getDuplicates,
  });

  if (isLoading) {
    return <div className="text-gray-500">加载中...</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">重复文件</h2>

      {data?.groups?.length ? (
        <div className="space-y-4">
          {data.groups.map((group, i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex justify-between items-center mb-3">
                <div className="text-sm text-gray-500">
                  重复组 · {group.count} 个文件 · {formatSize(group.size_bytes)}
                </div>
                <div className="text-xs text-gray-400 font-mono truncate max-w-[200px]">
                  {group.sha256.slice(0, 16)}...
                </div>
              </div>
              <div className="space-y-1">
                {group.files.map((f) => (
                  <div key={f.id} className="text-sm text-gray-700 bg-gray-50 rounded px-3 py-2 truncate">
                    {f.current_path}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-400">
          暂无重复文件
        </div>
      )}
    </div>
  );
}

function formatSize(bytes: number): string {
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(1)} KB`;
  return `${bytes} B`;
}
