import { createContext, useContext, useState, ReactNode } from "react";
import { useMutation } from "@tanstack/react-query";
import { createRuleDraft } from "../services/api";
import toast from "react-hot-toast";

interface DraftContextType {
  prompt: string;
  setPrompt: (v: string) => void;
  draftId: number | null;
  setDraftId: (id: number | null) => void;
  abortController: AbortController | null;
  setAbortController: (c: AbortController | null) => void;
  draftMutation: any;
  handleGenerate: () => void;
  handleCancel: () => void;
}

const DraftContext = createContext<DraftContextType | null>(null);

export function DraftProvider({ children }: { children: ReactNode }) {
  const [prompt, setPrompt] = useState("");
  const [draftId, setDraftId] = useState<number | null>(null);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const draftMutation = useMutation({
    mutationFn: (variables: { prompt: string; signal?: AbortSignal }) =>
      createRuleDraft(variables.prompt, variables.signal),
    onSuccess: (data) => {
      setDraftId(data.draft_id);
      toast.success("规则草案生成成功！");
    },
    onError: (err: any) => {
      if (err.name === 'AbortError' || err.message?.includes('aborted')) {
          return; // Silent for user cancel
      }
      toast.error(`生成失败: ${err.message}`);
    }
  });

  const handleGenerate = () => {
    const controller = new AbortController();
    setAbortController(controller);
    draftMutation.mutate({ prompt, signal: controller.signal });
  };

  const handleCancel = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      toast.success("生成已中止");
    }
  };

  return (
    <DraftContext.Provider
      value={{
        prompt,
        setPrompt,
        draftId,
        setDraftId,
        abortController,
        setAbortController,
        draftMutation,
        handleGenerate,
        handleCancel,
      }}
    >
      {children}
    </DraftContext.Provider>
  );
}

export function useDraftContext() {
  const context = useContext(DraftContext);
  if (!context) {
    throw new Error("useDraftContext must be used within a DraftProvider");
  }
  return context;
}
