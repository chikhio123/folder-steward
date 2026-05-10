import { getFileKind, type FileKind } from "../../utils/fileType";
import {
  File,
  FileImage,
  FileText,
  FileCode,
  FileVideo,
  FileAudio,
  FileArchive,
} from "lucide-react";
import { twMerge } from "tailwind-merge";

interface FileIconProps {
  ext: string | null;
  className?: string;
}

const kindToIcon: Record<FileKind, React.ElementType> = {
  image: FileImage,
  video: FileVideo,
  audio: FileAudio,
  archive: FileArchive,
  code: FileCode,
  text: FileText,
  unknown: File,
};

const kindToColorClass: Record<FileKind, string> = {
  image: "text-amber-500",
  video: "text-rose-500",
  audio: "text-purple-500",
  archive: "text-amber-600",
  code: "text-emerald-500",
  text: "text-blue-500",
  unknown: "text-slate-400",
};

export function FileIcon({ ext, className }: FileIconProps) {
  const kind = getFileKind(ext);
  const IconComponent = kindToIcon[kind];
  const colorClass = kindToColorClass[kind];

  return <IconComponent className={twMerge("w-5 h-5 shrink-0", colorClass, className)} />;
}
