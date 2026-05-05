import {
  File,
  FileImage,
  FileText,
  FileCode,
  FileVideo,
  FileAudio,
  FileArchive,
} from "lucide-react";

export function formatSize(bytes: number): string {
  if (bytes >= 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(1)} GB`;
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(1)} KB`;
  return `${bytes} B`;
}

export function getFileIcon(ext: string | null) {
  if (!ext) return <File className="w-5 h-5 text-slate-400 shrink-0" />;
  const lExt = ext.toLowerCase();

  if (['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'].includes(lExt)) {
    return <FileImage className="w-5 h-5 text-amber-500 shrink-0" />;
  }
  if (['.mp4', '.mov', '.avi', '.mkv'].includes(lExt)) {
    return <FileVideo className="w-5 h-5 text-rose-500 shrink-0" />;
  }
  if (['.mp3', '.wav', '.flac'].includes(lExt)) {
    return <FileAudio className="w-5 h-5 text-purple-500 shrink-0" />;
  }
  if (['.zip', '.rar', '.7z', '.tar', '.gz'].includes(lExt)) {
    return <FileArchive className="w-5 h-5 text-amber-600 shrink-0" />;
  }
  if (['.js', '.ts', '.py', '.java', '.c', '.cpp', '.rs', '.go', '.html', '.css', '.json'].includes(lExt)) {
    return <FileCode className="w-5 h-5 text-emerald-500 shrink-0" />;
  }
  if (['.txt', '.md', '.doc', '.docx', '.pdf'].includes(lExt)) {
    return <FileText className="w-5 h-5 text-blue-500 shrink-0" />;
  }

  return <File className="w-5 h-5 text-slate-400 shrink-0" />;
}