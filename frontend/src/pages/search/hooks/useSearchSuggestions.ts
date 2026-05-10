import { useState, useEffect, useCallback, useRef } from 'react';
import { getSearchSuggestions } from '../../../services/api';

const HISTORY_KEY = 'fs_search_history';

export interface SuggestionItem {
  type: 'history' | 'filename';
  text: string;
  file_id?: number;
  path?: string;
}

export function useSearchSuggestions() {
  const [history, setHistory] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const lastRequestSeq = useRef(0);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(HISTORY_KEY);
      if (stored) {
        setHistory(JSON.parse(stored));
      }
    } catch (e) {}
  }, []);

  const saveToHistory = useCallback((query: string) => {
    const q = query.trim();
    if (!q) return;

    setHistory(prev => {
      const newHistory = [q, ...prev.filter(item => item.toLowerCase() !== q.toLowerCase())].slice(0, 10);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(newHistory));
      return newHistory;
    });
  }, []);

  const clearHistory = useCallback(() => {
    setHistory([]);
    localStorage.removeItem(HISTORY_KEY);
  }, []);

  const fetchSuggestions = useCallback(async (query: string) => {
    const q = query.trim();
    if (q.length < 2) {
      lastRequestSeq.current++; // 废弃之前的进行中请求
      setSuggestions([]);
      setIsLoading(false);
      return;
    }

    const seq = ++lastRequestSeq.current;
    setIsLoading(true);
    try {
      const data = await getSearchSuggestions(q);
      if (seq !== lastRequestSeq.current) return;
      setSuggestions(data.items.map(item => ({ ...item, type: item.type as 'history' | 'filename' })));
    } catch (e) {
      console.error('Failed to fetch suggestions:', e);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    history,
    suggestions,
    isLoading,
    saveToHistory,
    clearHistory,
    fetchSuggestions,
    setSuggestions
  };
}
