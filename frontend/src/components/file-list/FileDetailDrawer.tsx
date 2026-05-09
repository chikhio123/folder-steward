import { twMerge } from "tailwind-merge";
import FileDetailPanel from "../FileDetailPanel";
import type { FileRecord } from "../../types";

export interface FileDetailDrawerProps {
  selectedFile: FileRecord | null;
  onClose: () => void;
}

export function FileDetailDrawer({ selectedFile, onClose }: FileDetailDrawerProps) {
  return (
    <>
      <div
        className={twMerge(
          "fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40 transition-opacity duration-300",
          selectedFile ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={onClose}
      />
      <div
        className={twMerge(
          "fixed inset-y-0 right-0 w-[400px] z-50 transform transition-transform duration-300 ease-in-out",
          selectedFile ? "translate-x-0" : "translate-x-full"
        )}
      >
        {selectedFile && <FileDetailPanel file={selectedFile} onClose={onClose} />}
      </div>
    </>
  );
}