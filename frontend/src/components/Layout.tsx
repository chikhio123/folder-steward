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
  BrainCircuit
} from "lucide-react";
import { twMerge } from "tailwind-merge";

const navItems = [
  { to: "/", label: "概览", icon: LayoutDashboard },
  { to: "/scan", label: "扫描", icon: Search },
  { to: "/search", label: "全局搜索", icon: Search },
  { to: "/files", label: "文件列表", icon: Files },
  { to: "/duplicates", label: "重复文件", icon: Copy },
  { to: "/smart-organize", label: "AI 智能大盘", icon: BrainCircuit },
  { to: "/ai-rules", label: "AI 规则生成", icon: Sparkles },
  { to: "/suggestions", label: "整理建议", icon: Wand2 },
  { to: "/operations", label: "操作历史", icon: History },
  { to: "/settings", label: "设置", icon: Settings },
];

export default function Layout() {
  return (
    <div className="h-screen w-screen bg-slate-50 flex overflow-hidden select-none">
      {/* Sidebar */}
      <nav className="w-64 bg-white/80 backdrop-blur-xl border-r border-slate-200 flex flex-col shadow-sm z-10 relative">
        {/* Electron Titlebar Drag Region */}
        <div className="h-10 w-full" style={{ WebkitAppRegion: "drag" } as React.CSSProperties} />

        <div className="px-6 pb-4">
          <h1 className="text-xl font-semibold text-slate-800 tracking-tight flex items-center gap-2">
            <span className="bg-blue-600 w-2 h-2 rounded-full inline-block"></span>
            Folder Steward
          </h1>
        </div>

        <div className="flex-1 flex flex-col gap-1 px-3 overflow-y-auto mt-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                twMerge(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ease-in-out cursor-pointer",
                  isActive
                    ? "bg-blue-50 text-blue-700 font-medium shadow-sm ring-1 ring-blue-100"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                )
              }
            >
              <item.icon className="w-4 h-4" strokeWidth={2.5} />
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full bg-slate-50/50 relative">
        {/* Top Drag Region for Main Content */}
        <div className="h-10 w-full shrink-0" style={{ WebkitAppRegion: "drag" } as React.CSSProperties} />
        <div className="flex-1 overflow-y-auto px-8 pb-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
