import { useState, useRef, useEffect } from "react";
import { ChevronDown, Check } from "lucide-react";
import { twMerge } from "tailwind-merge";

interface Option {
  value: string;
  label: string;
}

interface CustomSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: Option[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  icon?: React.ReactNode;
}

export function CustomSelect({
  value,
  onChange,
  options,
  placeholder = "请选择...",
  disabled = false,
  className,
  icon
}: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((o) => o.value === value);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [isOpen]);

  return (
    <div className={twMerge("relative", className)} ref={containerRef}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={twMerge(
          "w-full flex items-center justify-between gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-300",
          "bg-white/80 backdrop-blur-xl border border-slate-200/80 text-slate-700",
          "hover:bg-white hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500/50",
          disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
          isOpen ? "ring-2 ring-blue-500/50 border-blue-400 bg-white" : ""
        )}
      >
        <div className="flex items-center gap-2 min-w-0">
          {icon && <span className="text-slate-400 shrink-0">{icon}</span>}
          <span className="truncate">
            {selectedOption ? selectedOption.label : <span className="text-slate-400">{placeholder}</span>}
          </span>
        </div>
        <ChevronDown
          className={twMerge(
            "w-4 h-4 text-slate-400 shrink-0 transition-transform duration-300",
            isOpen ? "rotate-180" : ""
          )}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-2 py-1 bg-white/90 backdrop-blur-2xl border border-slate-200/80 rounded-xl shadow-xl shadow-slate-200/50 origin-top animation-fade-in max-h-60 overflow-y-auto custom-scrollbar">
          {options.length === 0 ? (
            <div className="px-4 py-3 text-sm text-slate-400 text-center">暂无选项</div>
          ) : (
            options.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className={twMerge(
                  "w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center justify-between",
                  value === option.value
                    ? "bg-blue-50/80 text-blue-700 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                )}
              >
                <span className="truncate">{option.label}</span>
                {value === option.value && <Check className="w-4 h-4 text-blue-600 shrink-0" />}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
