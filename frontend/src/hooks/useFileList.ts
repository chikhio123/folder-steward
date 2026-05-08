import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getFiles, searchFiles } from '../services/api';
import type { FileRecord } from '../types';

export const useFileList = () => {
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState('');
  const [extension, setExtension] = useState('');
  const [sortBy, setSortBy] = useState('modified_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedFile, setSelectedFile] = useState<FileRecord | null>(null);
  const pageSize = 50;

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['files', page, keyword, extension, sortBy, sortOrder],
    queryFn: () => {
      const skip = (page - 1) * pageSize;
      if (keyword || extension) {
        return searchFiles({
          keyword: keyword || undefined,
          extension: extension || undefined,
          skip,
          limit: pageSize
        });
      }
      return getFiles({
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder
      });
    },
  });

  return {
    state: { page, keyword, extension, sortBy, sortOrder, selectedFile },
    actions: { setPage, setKeyword, setExtension, setSortBy, setSortOrder, setSelectedFile, refetch },
    query: { data, isLoading }
  };
};