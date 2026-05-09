import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Settings2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { listRules, updateRule, deleteRule } from '../../services/api';
import RuleCard from './RuleCard';

export default function RuleManageView() {
  const queryClient = useQueryClient();

  const { data: rulesList, isLoading: isRulesLoading } = useQuery({
    queryKey: ["rules", "all"],
    queryFn: () => listRules(false),
  });

  const toggleRuleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number, enabled: boolean }) => updateRule(id, { enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules", "all"] });
      toast.success("规则状态已更新");
    },
    onError: (err: any) => toast.error(`状态更新失败: ${err.message}`)
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (id: number) => deleteRule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules", "all"] });
      toast.success("规则已永久删除");
    },
    onError: (err: any) => toast.error(`删除失败: ${err.message}`)
  });

  return (
    <div className="pb-8 relative z-10 flex flex-col">
      {isRulesLoading ? (
        <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20 space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <p>加载规则列表中...</p>
        </div>
      ) : rulesList && rulesList.length > 0 ? (
        <div className="space-y-4">
          {rulesList.map((r: any) => (
            <RuleCard 
              key={r.id} 
              rule={r} 
              onToggle={(id: number, enabled: boolean) => toggleRuleMutation.mutate({ id, enabled })}
              onDelete={(id: number) => deleteRuleMutation.mutate(id)}
              isToggling={toggleRuleMutation.isPending}
              isDeleting={deleteRuleMutation.isPending}
            />
          ))}
        </div>
      ) : (
        <div className="h-full flex flex-col items-center justify-center text-slate-400 py-20">
          <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
            <Settings2 className="w-8 h-8 text-slate-300" />
          </div>
          <p className="font-medium text-slate-500">暂无任何自动化规则</p>
          <p className="text-sm mt-1">请前往“写新规则”页面，让 AI 帮您生成</p>
        </div>
      )}
    </div>
  );
}