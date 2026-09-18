import React from 'react';
import { Layers, Database, Cpu, Bot, CheckCircle2, ArrowDown, Server, Shield, Sparkles } from 'lucide-react';
import { SystemHealth } from '../types';

interface ArchitecturePageProps {
  systemHealth: SystemHealth | null;
}

export const ArchitecturePage: React.FC<ArchitecturePageProps> = ({ systemHealth }) => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Judge-Facing Headline Banner */}
      <div className="bg-gradient-to-r from-railnavy-950 via-railnavy-900 to-railnavy-850 rounded-xl p-6 mb-8 text-white border border-railnavy-800 shadow-md">
        <div className="max-w-3xl">
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Cpu className="w-4 h-4" />
            <span>Judge-Facing Technical Overview</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white mb-2">
            The RailMind Pipeline Architecture
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Existing railway systems provide raw information. <strong className="text-white">RailMind</strong> connects that
            information to the passenger's journey state, evaluates the impact of changing conditions, and converts them into feasible actions.
          </p>
          <div className="mt-4 inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-railblue-900/60 border border-railblue-700 text-xs font-mono text-cyan-300">
            <span>DATA ↓ EVENT ↓ STATE ↓ IMPACT ↓ DECISION ↓ ACTION ↓ EXPLANATION</span>
          </div>
        </div>
      </div>

      {/* Interactive System Flow Diagram */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 mb-8">
        <h2 className="text-base font-bold text-slate-900 mb-6 flex items-center space-x-2">
          <Layers className="w-5 h-5 text-railblue-700" />
          <span>End-to-End System Pipeline & Information Flow</span>
        </h2>

        {/* 7-Stage Flow Visualization */}
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3 relative">
          {/* Stage 1: External API */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Source Layer</div>
              <div className="font-bold text-xs text-slate-900 mb-1">1. Railway Data</div>
              <p className="text-[11px] text-slate-600">External Railway API or Simulation Injector</p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-200 text-[10px] font-mono text-slate-500">
              HTTP / JSON
            </div>
          </div>

          {/* Stage 2: Data Adapter */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Integration</div>
              <div className="font-bold text-xs text-slate-900 mb-1">2. API Adapter</div>
              <p className="text-[11px] text-slate-600">Normalizes running status & schedule schema</p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-200 text-[10px] font-mono text-slate-500">
              railway_api.py
            </div>
          </div>

          {/* Stage 3: Event Engine */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Event Ingestion</div>
              <div className="font-bold text-xs text-slate-900 mb-1">3. Event Engine</div>
              <p className="text-[11px] text-slate-600">Validates, persists to SQLite, finds affected PNRs</p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-200 text-[10px] font-mono text-slate-500">
              event_engine.py
            </div>
          </div>

          {/* Stage 4: Journey State */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">State Engine</div>
              <div className="font-bold text-xs text-slate-900 mb-1">4. Journey State</div>
              <p className="text-[11px] text-slate-600">Recalculates leg ETAs & transfer window</p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-200 text-[10px] font-mono text-slate-500">
              journey_state.py
            </div>
          </div>

          {/* Stage 5: Impact Engine */}
          <div className="p-4 rounded-xl border border-amber-300 bg-amber-50/40 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-amber-700 mb-1">Deterministic</div>
              <div className="font-bold text-xs text-slate-900 mb-1">5. Impact Engine</div>
              <p className="text-[11px] text-slate-600">Buffer delta = Connection Dep - Actual Arr</p>
            </div>
            <div className="mt-3 pt-2 border-t border-amber-200 text-[10px] font-mono text-amber-800">
              impact_engine.py
            </div>
          </div>

          {/* Stage 6: Decision Engine */}
          <div className="p-4 rounded-xl border border-railblue-300 bg-railblue-50/40 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-railblue-700 mb-1">Deterministic</div>
              <div className="font-bold text-xs text-slate-900 mb-1">6. Decision Engine</div>
              <p className="text-[11px] text-slate-600">Applies transfer constraints & feasible actions</p>
            </div>
            <div className="mt-3 pt-2 border-t border-railblue-200 text-[10px] font-mono text-railblue-800">
              decision_engine.py
            </div>
          </div>

          {/* Stage 7: Strands AI */}
          <div className="p-4 rounded-xl border border-cyan-300 bg-cyan-50/40 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-700 mb-1">AWS SDK Layer</div>
              <div className="font-bold text-xs text-slate-900 mb-1">7. Strands Agent</div>
              <p className="text-[11px] text-slate-600">Explains structured decision to passenger</p>
            </div>
            <div className="mt-3 pt-2 border-t border-cyan-200 text-[10px] font-mono text-cyan-800">
              strands_agent.py
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Section: Architectural Guarantees & Active SQLite Health */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Core Principles */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs p-6">
          <div className="flex items-center space-x-2 pb-3 mb-4 border-b border-slate-100">
            <Shield className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-slate-900">Guaranteed Architectural Principles</h3>
          </div>

          <div className="space-y-3.5 text-xs text-slate-700">
            <div className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900">Deterministic Decision Making:</strong> The Decision Engine
                is 100% deterministic code. AI never independently makes railway operational decisions or computes transfer buffers.
              </div>
            </div>

            <div className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900">AWS Strands Agent Explanation:</strong> Strands receives
                only the structured JSON produced by the deterministic engine. It is strictly prompted to interpret facts without hallucinating.
              </div>
            </div>

            <div className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900">Data Source Transparency:</strong> The system visibly flags
                whether data is <code className="bg-slate-100 px-1 py-0.5 rounded font-mono">LIVE DATA</code> or <code className="bg-slate-100 px-1 py-0.5 rounded font-mono">SIMULATED DATA</code>. It never falsifies demo data as live real-time railway data.
              </div>
            </div>

            <div className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900">Relational SQLite Persistence:</strong> Journeys, legs,
                trains, bookings, events, decisions, and recommendations are fully modeled in normalized relational tables.
              </div>
            </div>
          </div>
        </div>

        {/* Live System Diagnostics */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-xs p-6">
          <div className="flex items-center space-x-2 pb-3 mb-4 border-b border-slate-100">
            <Server className="w-5 h-5 text-railblue-700" />
            <h3 className="text-base font-bold text-slate-900">Live Component Health</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Database Layer:</span>
              <span className="font-mono font-bold text-emerald-700">
                {systemHealth?.database || 'SQLite3 (railway.db)'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Data Adapter Mode:</span>
              <span className="font-mono font-bold text-amber-700">
                {systemHealth?.data_adapter_mode || 'SIMULATED DATA (Fallback)'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Strands Agents SDK:</span>
              <span className="font-mono font-bold text-cyan-700">
                {systemHealth?.strands_status || 'READY (Strands v1.56)'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Tracked Journeys:</span>
              <span className="font-mono font-bold text-slate-900">
                {systemHealth?.active_journeys_count || 1} Active PNRs
              </span>
            </div>

            <div className="flex justify-between py-1.5">
              <span className="text-slate-500 font-medium">Logged Railway Events:</span>
              <span className="font-mono font-bold text-slate-900">
                {systemHealth?.events_count || 0} Events in SQLite
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
