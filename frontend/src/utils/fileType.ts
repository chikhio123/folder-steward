export type FileKind = "image" | "video" | "audio" | "archive" | "code" | "text" | "unknown";

export function getFileKind(ext: string | null): FileKind {
  if (!ext) return "unknown";
  const lExt = ext.toLowerCase();

  if (['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'].includes(lExt)) return "image";
  if (['.mp4', '.mov', '.avi', '.mkv'].includes(lExt)) return "video";
  if (['.mp3', '.wav', '.flac'].includes(lExt)) return "audio";
  if (['.zip', '.rar', '.7z', '.tar', '.gz'].includes(lExt)) return "archive";
  if (['.js', '.ts', '.py', '.java', '.c', '.cpp', '.rs', '.go', '.html', '.css', '.json'].includes(lExt)) return "code";
  if (['.txt', '.md', '.doc', '.docx', '.pdf'].includes(lExt)) return "text";

  return "unknown";
}
