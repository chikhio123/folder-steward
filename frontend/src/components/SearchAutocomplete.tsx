import React, { useState, useEffect, useRef } from 'react';
import { Search as SearchIcon, Clock, FileBox, X, Loader2 } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useSearchSuggestions, SuggestionItem } from '../hooks/useSearchSuggestions';

interface SearchAutocompleteProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: (val: string) => void;
  onSelectFile?: (path: string) => void;
}

export function SearchAutocomplete({ value, onChange, onSubmit }: SearchAutocompleteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    history,
    suggestions,
    isLoading,
    saveToHistory,
    clearHistory,
    fetchSuggestions,
    setSuggestions
  } = useSearchSuggestions();

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Debounce fetching suggestions
  useEffect(() => {
    if (value.trim().length >= 2) {
      const timer = setTimeout(() => {
        fetchSuggestions(value);
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setSuggestions([]);
    }
  }, [value, fetchSuggestions, setSuggestions]);

  // Reset active index when list changes
  useEffect(() => {
    setActiveIndex(-1);
  }, [value, suggestions, history]);

  const displayItems: SuggestionItem[] = value.trim().length < 2
    ? history.slice(0, 5).map(h => ({ type: 'history', text: h }))
    : suggestions;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < displayItems.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : displayItems.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < displayItems.length) {
        handleSelect(displayItems[activeIndex]);
      } else {
        handleSearchSubmit(value);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      inputRef.current?.blur();
    }
  };

  const handleSearchSubmit = (searchVal: string) => {
    if (!searchVal.trim()) return;
    saveToHistory(searchVal);
    setIsOpen(false);
    onSubmit(searchVal);
    inputRef.current?.blur();
  };

  const handleSelect = (item: SuggestionItem) => {
    if (item.type === 'history') {
      onChange(item.text);
      handleSearchSubmit(item.text);
    } else if (item.type === 'filename') {
      onChange(item.text);
      saveToHistory(item.text);
      setIsOpen(false);
      onSubmit(item.text);
      // Optional: If we want to instantly open the file location, uncomment below:
      // if (item.path && onSelectFile) onSelectFile(item.path);
    }
  };

  const highlightMatch = (text: string, query: string) => {
    if (!query) return text;
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return (
      <>
        {parts.map((part, i) =>
          part.toLowerCase() === query.toLowerCase()
            ? <strong key={i} className="text-blue-600">{part}</strong>
            : part
        )}
      </>
    );
  };

  return (
    <div className="relative flex-1 min-w-[240px] z-50" ref={containerRef}>
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <SearchIcon className="h-5 w-5 text-blue-500" />
      </div>

      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          if (!isOpen) setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={handleKeyDown}
        placeholder="输入搜索关键词..."
        className="w-full bg-white/60 backdrop-blur-md border border-slate-200/60 text-slate-800 rounded-xl pl-11 pr-10 py-3 text-base font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all placeholder:text-slate-400 shadow-sm"
      />

      {value && (
        <button
          onClick={() => { onChange(''); inputRef.current?.focus(); }}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}

      {isOpen && (displayItems.length > 0 || isLoading) && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white/95 backdrop-blur-2xl border border-slate-200/80 rounded-xl shadow-xl shadow-slate-200/50 overflow-hidden animation-fade-in py-2">
          {isLoading && displayItems.length === 0 ? (
            <div className="px-4 py-3 flex items-center gap-2 text-sm text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
              正在查找相关文件...
            </div>
          ) : (
            <>
              {value.trim().length < 2 && history.length > 0 && (
                <div className="px-4 py-1.5 flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  最近搜索
                  <button onClick={clearHistory} className="hover:text-rose-500 transition-colors cursor-pointer text-[10px]">清空</button>
                </div>
              )}

              {displayItems.map((item, idx) => (
                <button
                  key={`${item.type}-${item.text}-${idx}`}
                  className={twMerge(
                    "w-full px-4 py-2.5 flex items-center gap-3 text-left transition-colors",
                    activeIndex === idx ? "bg-blue-50/80" : "hover:bg-slate-50"
                  )}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setActiveIndex(idx)}
                >
                  {item.type === 'history' ? (
                    <Clock className="w-4 h-4 text-slate-400 shrink-0" />
                  ) : (
                    <FileBox className="w-4 h-4 text-blue-400 shrink-0" />
                  )}

                  <div className="flex flex-col min-w-0 flex-1">
                    <span className="text-sm font-medium text-slate-700 truncate">
                      {item.type === 'filename' ? highlightMatch(item.text, value.trim()) : item.text}
                    </span>
                    {item.path && (
                      <span className="text-xs text-slate-400 truncate mt-0.5">
                        {item.path}
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
