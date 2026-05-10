import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Wand2, Sparkles, Settings2 } from "lucide-react";
import { twMerge } from "tailwind-merge";
import { listRules } from "../../services/api";
import RuleCreateView from "./components/RuleCreateView";
import RuleManageView from "./components/RuleManageView";

export default function AiRuleDraftPage() {
  const [activeTab, setActiveTab] = useState<"create" | "manage">("create");

  // Keep this query to fetch count for the badge
  const { data: rulesList } = useQuery({
    queryKey: ["rules", "all"],
    queryFn: () => listRules(false),
  });

  return (
    <div className="max-w-4xl mx-auto animation-fade-in flex flex-col h-full relative">
      {/* 背景光晕 */}
      <div className="absolute top-[-10%] right-[-10%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="mb-6 shrink-0 relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-400 tracking-tight flex items-center gap-2 pb-1">
            <Sparkles className="w-8 h-8 text-blue-500 shrink-0" />
            AI 自动化规则
          </h2>
          <p className="text-slate-500 mt-1 font-medium">让 AI 把您的整理习惯转化成自动化规则，一劳永逸。</p>
        </div>

        {/* 苹果风 Segmented Control */}
        <div className="flex bg-slate-200/50 p-1 rounded-xl w-fit">
          <button
            onClick={() => setActiveTab("create")}
            className={twMerge(
              "px-5 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2",
              activeTab === "create"
                ? "bg-white text-blue-600 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            <Wand2 className="w-4 h-4" />
            写新规则
          </button>
          <button
            onClick={() => setActiveTab("manage")}
            className={twMerge(
              "px-5 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2",
              activeTab === "manage"
                ? "bg-white text-blue-600 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            <Settings2 className="w-4 h-4" />
            管理规则
            {rulesList && rulesList.length > 0 && (
              <span className={twMerge(
                "px-1.5 py-0.5 rounded-md text-[10px]",
                activeTab === "manage" ? "bg-blue-100 text-blue-700" : "bg-slate-200 text-slate-500"
              )}>
                {rulesList.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {activeTab === "create" ? <RuleCreateView /> : <RuleManageView />}
    </div>
  );
}

