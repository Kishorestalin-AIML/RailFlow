import React from 'react';
import { Train, Search, GitCompare, Bell, Cpu, PlusCircle } from 'lucide-react';
import { SystemHealth } from '../types';

interface NavbarProps {
  activeTab: 'journey' | 'search' | 'alternatives' | 'notifications' | 'architecture';
  setActiveTab: (tab: 'journey' | 'search' | 'alternatives' | 'notifications' | 'architecture') => void;
  systemHealth: SystemHealth | null;
  dataSource: string;
  onOpenRegistration: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  systemHealth,
  dataSource,
  onOpenRegistration
}) => {
  const isLive = dataSource.includes('LIVE');

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Logo */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('journey')}>
            <div className="h-10 w-10 rounded-xl bg-cyan-600 flex items-center justify-center text-white shadow-md shadow-cyan-600/30">
              <Train className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">RailMind</span>
                <span className="text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                  Live Intelligence
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Real-Time Railway Journey Intelligence & Decision Engine</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              onClick={() => setActiveTab('journey')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center space-x-2 ${
                activeTab === 'journey'
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Train className="h-4 w-4" />
              <span>My Journey</span>
            </button>

            <button
              onClick={() => setActiveTab('search')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center space-x-2 ${
                activeTab === 'search'
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Search className="h-4 w-4" />
              <span>Find Trains</span>
            </button>

            <button
              onClick={() => setActiveTab('alternatives')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center space-x-2 ${
                activeTab === 'alternatives'
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <GitCompare className="h-4 w-4 text-cyan-400" />
              <span>Alternative Plans</span>
            </button>

            <button
              onClick={() => setActiveTab('notifications')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center space-x-2 ${
                activeTab === 'notifications'
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Bell className="h-4 w-4 text-emerald-400" />
              <span>Notifications</span>
            </button>

            <button
              onClick={() => setActiveTab('architecture')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center space-x-2 ${
                activeTab === 'architecture'
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Cpu className="h-4 w-4 text-purple-400" />
              <span>System</span>
            </button>
          </nav>

          {/* Right Controls: Start New Journey + Live RailRadar indicator */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenRegistration}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold border border-slate-700 transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>New Journey</span>
            </button>

            {/* Live Indicator per Section 25 */}
            <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-semibold border ${
              isLive
                ? 'bg-emerald-950/80 text-emerald-400 border-emerald-500/40'
                : 'bg-cyan-950/80 text-cyan-300 border-cyan-800/60'
            }`}>
              <span className={`h-2 w-2 rounded-full ${isLive ? 'bg-emerald-400' : 'bg-cyan-400'} animate-pulse`}></span>
              <div className="flex flex-col text-[11px] leading-tight">
                <span className="font-bold">{isLive ? '● LIVE' : '● RAILRADAR'}</span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {systemHealth?.last_updated ? `Updated ${systemHealth.last_updated}` : 'Live Polling'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
