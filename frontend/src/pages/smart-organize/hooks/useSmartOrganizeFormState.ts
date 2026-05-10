import { useState } from 'react';

export const useSmartOrganizeFormState = () => {
  const [archiveRoot, setArchiveRoot] = useState(() => localStorage.getItem("fs_last_archive_root") || "D:/Archive");
  const [scope, setScope] = useState("all");
  const [minConfidence, setMinConfidence] = useState<number | string>(0.65);
  const [showExcludeModal, setShowExcludeModal] = useState(false);

  return {
    archiveRoot,
    setArchiveRoot,
    scope,
    setScope,
    minConfidence,
    setMinConfidence,
    showExcludeModal,
    setShowExcludeModal
  };
};