import { useMutation } from "@tanstack/react-query";
import { createRuleDraft } from "../services/api";
import toast from "react-hot-toast";

interface UseRuleDraftMutationOptions {
  onSuccess?: (draftId: number) => void;
  onSettled?: () => void;
}

export const useRuleDraftMutation = (options?: UseRuleDraftMutationOptions) => {
  return useMutation({
    mutationFn: (variables: { prompt: string; signal?: AbortSignal }) =>
      createRuleDraft(variables.prompt, variables.signal),
    onSuccess: (data) => {
      toast.success("规则草案生成成功！");
      if (options?.onSuccess) {
        options.onSuccess(data.draft_id);
      }
    },
    onError: (err: any) => {
      if (err.name === 'AbortError' || err.message?.includes('aborted')) {
        return; // Silent for user cancel
      }
      toast.error(`生成失败: ${err.message}`);
    },
    onSettled: () => {
      if (options?.onSettled) {
        options.onSettled();
      }
    }
  });
};
