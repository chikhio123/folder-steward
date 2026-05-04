import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "概览" },
  { to: "/scan", label: "扫描" },
  { to: "/files", label: "文件列表" },
  { to: "/duplicates", label: "重复文件" },
  { to: "/suggestions", label: "整理建议" },
  { to: "/operations", label: "操作历史" },
  { to: "/settings", label: "设置" },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <nav className="w-56 bg-white border-r border-gray-200 p-4 flex flex-col gap-1">
        <h1 className="text-lg font-bold text-gray-800 mb-4 px-3">Folder Steward</h1>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-blue-50 text-blue-700 font-medium"
                  : "text-gray-600 hover:bg-gray-100"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
