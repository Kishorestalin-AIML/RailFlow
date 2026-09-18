import React from 'react';
import { Train, Radio, Cpu, Activity, Search, ShieldCheck } from 'lucide-react';
import { SystemHealth } from '../types';

interface NavbarProps {
  activeTab: 'journey' | 'search' | 'simulation' | 'architecture';
  setActiveTab: (tab: 'journey' | 'search' | 'simulation' | 'architecture') => void;
  systemHealth: SystemHealth | null;
  dataSource: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  systemHealth,
  dataSource
}) => {
  const isLive = dataSource === 'LIVE DATA';

  return (
    <header className="bg-railnavy-900 border-b border-railnavy-800 text-white sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Logo */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('journey')}>
            <div className="h-10 w-10 rounded-lg bg-railblue-700 flex items-center justify-center text-white shadow-inner">
              <Train className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">RailMind</span>
                <span className="text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-railblue-900 text-railblue-400 border border-railblue-700">
                  Track 1 Intel
                </span>
              </div>
              <p className="text-xs text-slate-400">Railway Passenger Intelligence & Decision Engine</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              onClick={() => setActiveTab('journey')}
              className={`px-3.5 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
                activeTab === 'journey'
                  ? 'bg-railblue-700 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-railnavy-800'
              }`}
            >
              <Train className="h-4 w-4" />
              <span>My Journey</span>
            </button>

            <button
              onClick={() => setActiveTab('search')}
              className={`px-3.5 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
                activeTab === 'search'
                  ? 'bg-railblue-700 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-railnavy-800'
              }`}
            >
              <Search className="h-4 w-4" />
              <span>Train Search</span>
            </button>

            <button
              onClick={() => setActiveTab('simulation')}
              className={`px-3.5 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
                activeTab === 'simulation'
                  ? 'bg-railblue-700 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-railnavy-800'
              }`}
            >
              <Activity className="h-4 w-4 text-amber-400" />
              <span>Simulation Console</span>
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-signal-pulse"></span>
            </button>

            <button
              onClick={() => setActiveTab('architecture')}
              className={`px-3.5 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
                activeTab === 'architecture'
                  ? 'bg-railblue-700 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-railnavy-800'
              }`}
            >
              <Cpu className="h-4 w-4 text-cyan-400" />
              <span>Architecture & Flow</span>
            </button>
          </nav>

          {/* Right Status Badge */}
          <div className="flex items-center space-x-3">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold border ${
              isLive
                ? 'bg-emerald-950/80 text-emerald-400 border-emerald-600'
                : 'bg-amber-950/80 text-amber-400 border-amber-600'
            }`}>
              <span className={`h-2 w-2 rounded-full ${isLive ? 'bg-emerald-400' : 'bg-amber-400'} animate-signal-pulse`}></span>
              <span>{isLive ? '● LIVE DATA' : '● SIMULATED DATA'}</span>
            </div>

            <div className="hidden lg:flex flex-col text-right">
              <span className="text-[11px] text-slate-400">Last updated</span>
              <span className="text-xs font-mono font-medium text-slate-200">
                {systemHealth?.last_updated || 'Active Sync'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
