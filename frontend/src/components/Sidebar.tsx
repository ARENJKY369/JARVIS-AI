import { MessageSquare, BarChart3, Mic, Cpu, X } from 'lucide-react';

interface SidebarProps {
  open: boolean;
  activeTab: 'chat' | 'status' | 'voice';
  onTabChange: (tab: 'chat' | 'status' | 'voice') => void;
  onToggle: () => void;
}

const tabs = [
  { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
  { id: 'voice' as const, label: 'Voice', icon: Mic },
  { id: 'status' as const, label: 'Status', icon: BarChart3 },
];

export function Sidebar({ open, activeTab, onTabChange, onToggle }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-iron-900 border-r border-iron-800 transform transition-transform duration-300 ease-in-out ${
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-20 xl:w-64'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-iron-800">
          <div className="flex items-center gap-2">
            <Cpu className="w-6 h-6 text-jarvis-400" />
            <span className="font-bold text-lg tracking-wider lg:hidden xl:block">JARVIS</span>
          </div>
          <button onClick={onToggle} className="lg:hidden p-1 rounded hover:bg-iron-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-3 space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-jarvis-500/10 text-jarvis-400 border border-jarvis-500/20'
                    : 'text-iron-400 hover:bg-iron-800 hover:text-iron-200'
                }`}
              >
                <Icon className="w-5 h-5 shrink-0" />
                <span className="lg:hidden xl:block">{tab.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-iron-800">
          <div className="text-xs text-iron-500 lg:hidden xl:block">
            <p>Offline-first AI OS</p>
            <p className="mt-0.5">Local LLM • Secure • Private</p>
          </div>
        </div>
      </aside>
    </>
  );
}
