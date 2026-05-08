import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSuggestions, generateSuggestions, updateSuggestion, executeSuggestions, bulkRejectSuggestions } from '../services/api';
import toast from 'react-hot-toast';

export const useSuggestions = () => {
  const queryClient = useQueryClient();
  const [archiveRoot, setArchiveRoot] = useState(() => localStorage.getItem("fs_last_archive_root") || "D:/Archive");
  const [filter, setFilter] = useState("pending");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editPath, setEditPath] = useState("");
  const [showConfirmCancel, setShowConfirmCancel] = useState(false);

  useEffect(() => {
    if (archiveRoot.trim()) {
      localStorage.setItem("fs_last_archive_root", archiveRoot.trim());
    }
  }, [archiveRoot]);

  const { data, isLoading } = useQuery({
    queryKey: ["suggestions", filter, page],
    queryFn: () => getSuggestions({ status: filter === "all" ? undefined : filter, page, page_size: 50 }),
  });

  const generateMutation = useMutation({
    mutationFn: () => generateSuggestions(archiveRoot),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setPage(1);
      setFilter("pending");
      toast.success(`成功生成 ${data.created_count} 条建议`);
    },
    onError: (err: any) => toast.error(`生成失败: ${err.message}`),
  });

  const acceptMutation = useMutation({
    mutationFn: (id: number) => updateSuggestion(id, { status: "accepted" }),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setSelected((prev) => new Set(prev).add(id));
      toast.success("已同意并选中");
    },
    onError: (err: any) => toast.error(`操作失败: ${err.message}`),
  });

  const rejectOneMutation = useMutation({
    mutationFn: (id: number) => updateSuggestion(id, { status: "rejected" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      toast.success("已拒绝该建议");
    },
    onError: (err: any) => toast.error(`拒绝失败: ${err.message}`),
  });

  const savePathMutation = useMutation({
    mutationFn: ({ id, path }: { id: number, path: string }) => updateSuggestion(id, { target_path: path }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setEditingId(null);
      toast.success("目标路径已更新");
    },
    onError: (err: any) => {
      toast.error(`保存失败: ${err.message}`);
    }
  });

  const executeMutation = useMutation({
    mutationFn: () => executeSuggestions(Array.from(selected)),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setSelected(new Set());
      if (data.failed_count > 0) {
        toast.error(`${data.success_count} 个成功，${data.failed_count} 个失败`);
      } else {
        toast.success(`成功执行 ${data.success_count} 条操作`);
      }
    },
    onError: (err: any) => toast.error(`执行出错: ${err.message}`),
  });

  const bulkRejectMutation = useMutation({
    mutationFn: () => bulkRejectSuggestions(filter === "all" ? "pending" : filter),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      setSelected(new Set());
      setPage(1);
      setShowConfirmCancel(false);
      toast.success(`已取消 ${data.rejected_count} 条建议`);
    },
    onError: (err: any) => {
      setShowConfirmCancel(false);
      toast.error(`取消失败: ${err.message}`);
    },
  });

  return {
    state: { archiveRoot, filter, page, selected, editingId, editPath, showConfirmCancel, data, isLoading },
    actions: { setArchiveRoot, setFilter, setPage, setSelected, setEditingId, setEditPath, setShowConfirmCancel },
    mutations: { generateMutation, acceptMutation, rejectOneMutation, savePathMutation, executeMutation, bulkRejectMutation }
  };
};