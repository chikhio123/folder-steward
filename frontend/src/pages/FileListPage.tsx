import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getFiles } from "../services/api";
import type { FileRecord } from "../types";

export default function FileListPage() {
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [extension, setExtension] = useState("");
  const [sortBy, setSortBy] = useState("modified_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const { data, isLoading } = useQuery({
    queryKey: ["files", page, keyword, extension, sortBy, sortOrder],
    queryFn: () =>
      getFiles({
        page,
        page_size: 50,
        keyword: keyword || undefined,
        extension: extension || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  });

  const totalPages = data ? Math.ceil(data.total / 50) : 1;

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">文件列表</h2>

      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4 flex gap-3 flex-wrap">
        <input
          type="text"
          value={keyword}
          onChange={(e) => { setKeyword(e.target.value); setPage(1); }}
          placeholder="搜索文件名..."
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm flex-1 min-w-[200px] focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          value={extension}
          onChange={(e) => { setExtension(e.target.value); setPage(1); }}
          placeholder="扩展名筛选 (如 .pdf)"
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm w-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm"
        >
          <option value="modified_at">修改时间</option>
          <option value="size_bytes">文件大小</option>
          <option value="filename">文件名</option>
        </select>
        <button
          onClick={() => setSortOrder((o) => (o === "asc" ? "desc" : "asc"))}
          className="px-3 py-1.5 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
        >
          {sortOrder === "asc" ? "↑ 升序" : "↓ 降序"}
        </button>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 text-gray-600 font-medium">文件名</th>
              <th className="text-left px-4 py-3 text-gray-600 font-medium">扩展名</th>
              <th className="text-right px-4 py-3 text-gray-600 font-medium">大小</th>
              <th className="text-left px-4 py-3 text-gray-600 font-medium">修改时间</th>
              <th className="text-left px-4 py-3 text-gray-600 font-medium">状态</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="text-center py-8 text-gray-400">加载中...</td></tr>
            ) : data?.items?.length ? (
              data.items.map((f: FileRecord) => (
                <tr key={f.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-800 max-w-md truncate">{f.filename}</td>
                  <td className="px-4 py-3 text-gray-500">{f.extension}</td>
                  <td className="px-4 py-3 text-right text-gray-600">{formatSize(f.size_bytes)}</td>
                  <td className="px-4 py-3 text-gray-500">{f.modified_at ? f.modified_at.slice(0, 19) : "-"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${f.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                      {f.status}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={5} className="text-center py-8 text-gray-400">暂无文件记录</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center mt-4 text-sm text-gray-500">
        <span>共 {data?.total ?? 0} 条</span>
        <div className="flex gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-40 hover:bg-gray-50"
          >
            上一页
          </button>
          <span className="px-3 py-1">{page} / {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-40 hover:bg-gray-50"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
}

function formatSize(bytes: number): string {
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(1)} KB`;
  return `${bytes} B`;
}
