import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  Files,
  Copy,
  Wand2,
  History,
  Settings,
  Sparkles,
  BrainCircuit,
  ChevronDown
} from "lucide-react";
import { twMerge } from "tailwind-merge";

const navGroups = [
  {
    title: "核心",
    items: [
      { to: "/", label: "概览", icon: LayoutDashboard },
      { to: "/scan", label: "库扫描", icon: Search },
      { to: "/search", label: "全局搜索", icon: Search },
    ]
  },
  {
    title: "AI 智能",
    items: [
      { to: "/smart-organize", label: "AI 智能大盘", icon: BrainCircuit },
      { to: "/ai-rules", label: "AI 规则生成", icon: Sparkles },
      { to: "/suggestions", label: "智能建议", icon: Wand2 },
    ]
  },
  {
    title: "文件",
    items: [
      { to: "/files", label: "文件库", icon: Files },
      { to: "/duplicates", label: "重复文件", icon: Copy },
      { to: "/operations", label: "操作历史", icon: History },
    ]
  },
  {
    title: "系统",
    items: [
      { to: "/settings", label: "设置", icon: Settings },
    ]
  }
];

export default function Layout() {
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  const toggleGroup = (title: string) => {
    setCollapsedGroups(prev => ({ ...prev, [title]: !prev[title] }));
  };

  return (
    <div className="h-screen w-screen bg-slate-50 flex overflow-hidden select-none">
      {/* Sidebar */}
      <nav className="w-64 bg-white/80 backdrop-blur-xl border-r border-slate-200 flex flex-col shadow-sm z-10 relative">
        {/* Electron Titlebar Drag Region */}
        <div className="h-10 w-full" style={{ WebkitAppRegion: "drag" } as React.CSSProperties} />

        <div className="px-6 pb-2">
          <h1 className="text-xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
            <span className="bg-blue-600 w-2.5 h-2.5 rounded-full inline-block"></span>
            Folder Steward
          </h1>
        </div>

        <div className="flex-1 flex flex-col gap-3 px-3 overflow-y-auto mt-4 pb-6">
          {navGroups.map((group, idx) => {
            const isCollapsed = collapsedGroups[group.title];
            return (
              <div key={idx}>
                <button
                  onClick={() => toggleGroup(group.title)}
                  className="w-full flex items-center justify-between px-3 py-1.5 mb-0.5 text-xs font-bold tracking-wider text-slate-400 uppercase hover:text-slate-600 transition-colors"
                >
                  {group.title}
                  <ChevronDown
                    className={twMerge(
                      "w-3.5 h-3.5 transition-transform duration-200",
                      isCollapsed ? "-rotate-90" : "rotate-0"
                    )}
                  />
                </button>
                <div
                  className={twMerge(
                    "grid transition-all duration-300 ease-in-out",
                    isCollapsed ? "grid-rows-[0fr] opacity-0" : "grid-rows-[1fr] opacity-100"
                  )}
                >
                  <div className="overflow-hidden flex flex-col gap-0.5">
                    {group.items.map((item) => (
                      <NavLink
                        key={item.to}
                        to={item.to}
                        end={item.to === "/"}
                        className={({ isActive }) =>
                          twMerge(
                            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-200 ease-in-out cursor-pointer",
                            isActive
                              ? "bg-blue-50 text-blue-700 font-semibold shadow-sm ring-1 ring-blue-100"
                              : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 font-medium"
                          )
                        }
                      >
                        <item.icon className="w-4 h-4" strokeWidth={2.5} />
                        {item.label}
                      </NavLink>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full bg-slate-50/50 relative min-w-0">
        {/* Top Drag Region for Main Content */}
        <div className="h-10 w-full shrink-0" style={{ WebkitAppRegion: "drag" } as React.CSSProperties} />
        <div className="flex-1 overflow-y-auto px-8 pb-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
