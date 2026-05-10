import { useFileList } from '../hooks/useFileList';
import { Pagination } from '../components/common/Pagination';
import { Loader2 } from "lucide-react";
import { FileFilterBar } from '../components/file-list/FileFilterBar';
import { FileTableHeader } from '../components/file-list/FileTableHeader';
import { FileTableRow } from '../components/file-list/FileTableRow';
import { FileEmptyState } from '../components/file-list/FileEmptyState';
import { FileDetailDrawer } from '../components/file-list/FileDetailDrawer';
import { PageHeader } from '../components/ui/PageHeader';
import { Card } from '../components/ui/Card';
import type { FileRecord } from "../types";

export default function FileListPage() {
  const { state, actions, query } = useFileList();
  const { page, keyword, extension, sortBy, sortOrder, selectedFile } = state;
  const { setPage, setKeyword, setExtension, setSortBy, setSortOrder, setSelectedFile } = actions;
  const { data, isLoading } = query;

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 50)) : 1;

  const handleOpenFolder = (path: string) => {
    if (window.electronAPI?.openInFolder) {
      window.electronAPI.openInFolder(path);
    } else {
      console.warn("Not running in Electron, cannot open folder.");
    }
  };

  const handleSortChange = (field: string) => {
    if (sortBy === field) {
      setSortOrder(o => (o === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(field);
      setSortOrder(field === "filename" ? "asc" : "desc");
    }
    setPage(1);
  };

  return (
    <div className="max-w-6xl mx-auto animation-fade-in flex flex-col relative min-h-full">
      {/* 背景光晕 */}
      <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="mb-6 shrink-0 z-20 bg-slate-50/80 backdrop-blur-xl border-b border-slate-200/50 pb-4 pt-2 -mx-4 px-4 sm:-mx-0 sm:px-0">
        <PageHeader 
          title="文件索引库" 
          description="浏览已建立索引的所有文件记录，支持多维度检索与排序。" 
          className="mb-0"
        />
      </div>

      <FileFilterBar 
        keyword={keyword}
        extension={extension}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onKeywordChange={(val) => { setKeyword(val); setPage(1); }}
        onExtensionChange={(val) => { setExtension(val); setPage(1); }}
        onSortByChange={(val) => { setSortBy(val); setPage(1); }}
        onSortOrderToggle={() => { setSortOrder(o => (o === "asc" ? "desc" : "asc")); setPage(1); }}
      />

      <Card variant="glass" className="relative flex flex-col mb-8 overflow-hidden">
        <FileTableHeader 
          sortBy={sortBy} 
          sortOrder={sortOrder} 
          onSortChange={handleSortChange} 
        />

        <div className="p-2">
          {isLoading ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p>加载文件中...</p>
            </div>
          ) : data?.items?.length ? (
            <div className="divide-y divide-slate-100/60">
              {data.items.map((f: FileRecord) => (
                <FileTableRow 
                  key={f.id} 
                  file={f} 
                  onSelect={setSelectedFile} 
                  onOpenFolder={handleOpenFolder} 
                />
              ))}
            </div>
          ) : (
            <FileEmptyState />
          )}
        </div>

        <Pagination currentPage={page} totalPages={totalPages} totalItems={data?.total || 0} onPageChange={setPage} />
      </Card>

      <FileDetailDrawer 
        selectedFile={selectedFile} 
        onClose={() => setSelectedFile(null)} 
      />
    </div>
  );
}