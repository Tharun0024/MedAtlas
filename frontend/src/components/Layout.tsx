import { ReactNode } from 'react'
import {
  LayoutDashboard,
  Users,
  AlertTriangle,
  Download,
  Info,
  Activity,
  UploadCloud,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

interface LayoutProps {
  children: ReactNode
}

interface NavItem {
  name: string
  path: string
  icon: ReactNode
}

// use real routes (with leading /)
const navItems: NavItem[] = [
  { name: 'About', path: '/', icon: <Info size={20} /> },
  { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
  { name: 'Providers', path: '/providers', icon: <Users size={20} /> },
  {
    name: 'Discrepancies',
    path: '/discrepancies',
    icon: <AlertTriangle size={20} />,
  },
  { name: 'Export', path: '/export', icon: <Download size={20} /> },
  { name: 'Upload', path: '/upload', icon: <UploadCloud size={20} /> },
]

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Activity size={24} strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">MedAtlas</h1>
              <p className="text-xs text-slate-400">Provider Validation</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                [
                  'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all',
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800',
                ].join(' ')
              }
            >
              {item.icon}
              <span className="font-medium">{item.name}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="text-xs text-slate-500">
            <p className="font-medium text-slate-400 mb-1">System Status</p>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span>All systems operational</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
