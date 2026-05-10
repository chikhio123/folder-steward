import { FolderSearch, Play, AlertCircle, Loader2, FolderInput } from "lucide-react";
import { useScanTask } from "../hooks/useScanTask";
import { ScanProgressCard } from "../components/ScanProgressCard";
import { ScanReportCard } from "../components/ScanReportCard";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";

export default function ScanPage() {
  const {
    path,
    setPath,
    isRunning,
    handleSelectDirectory,
    taskQuery,
    errorQuery,
    createMutation,
    cancelMutation
  } = useScanTask();

  const task = taskQuery.data;
  const errorData = errorQuery.data;

  return (
    <div className="max-w-4xl mx-auto animation-fade-in relative">
      {/* 背景光晕 */}
      <div className="absolute top-[-10%] right-[-10%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <PageHeader 
        title="扫描文件夹" 
        description="选择一个目录进行深度扫描，建立本地文件索引并生成整理建议。" 
        className="relative z-10" 
      />

      <Card variant="glass" className="p-8 mb-6 hover:shadow-md relative z-10">
        <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-3">
          <FolderSearch className="w-4 h-4 text-blue-600" />
          目标文件夹路径
        </label>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="例如：D:/Downloads 或 /Users/name/Downloads"
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400"
              disabled={isRunning}
            />
            {isRunning && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2">
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              </div>
            )}
            {!isRunning && window.electronAPI?.selectDirectory && (
              <button
                type="button"
                onClick={handleSelectDirectory}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="选择文件夹"
              >
                <FolderInput className="w-5 h-5" />
              </button>
            )}
          </div>
          <Button
            variant="primary"
            size="lg"
            onClick={() => createMutation.mutate()}
            disabled={!path.trim() || isRunning}
            className="min-w-[140px]"
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                准备中
              </>
            ) : (
              <>
                <Play className="w-4 h-4" fill="currentColor" />
                开始扫描
              </>
            )}
          </Button>
        </div>
        {createMutation.isError && (
          <div className="mt-3 flex items-center gap-2 text-rose-600 bg-rose-50 px-3 py-2 rounded-lg text-sm border border-rose-100">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <p>{(createMutation.error as Error).message}</p>
          </div>
        )}
      </Card>

      {task && (
        <ScanProgressCard 
          task={task} 
          onCancel={() => cancelMutation.mutate()} 
          isCancelling={cancelMutation.isPending} 
          cancelError={cancelMutation.error as Error}
        />
      )}

      {(task?.status === "completed" || task?.status === "failed") && (
        <ScanReportCard 
          task={task} 
          errorData={errorData} 
          onLoadErrors={() => errorQuery.refetch()} 
        />
      )}
    </div>
  );
}