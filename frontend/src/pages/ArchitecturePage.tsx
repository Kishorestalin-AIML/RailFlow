import React from 'react';
import { Layers, Database, Cpu, CheckCircle2, Server, Shield, Sparkles, MessageSquare, Mail, Radio } from 'lucide-react';
import { SystemHealth } from '../types';

interface ArchitecturePageProps {
  systemHealth: SystemHealth | null;
}

export const ArchitecturePage: React.FC<ArchitecturePageProps> = ({ systemHealth }) => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8 animate-fade-in">
      {/* Top Headline Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="max-w-3xl">
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Cpu className="w-4 h-4" />
            <span>Technical Architecture & Intelligence Pipeline</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-2">
            RailMind — Real-Time Railway Journey Intelligence
          </h1>
          <p className="text-xs text-slate-300 leading-relaxed">
            RailMind is an <strong className="text-cyan-300">additive intelligence layer</strong> over Indian Railway information systems.
            It ingests live running data from the <strong className="text-white">RailRadar API</strong>, tracks passenger journey states,
            evaluates connection risks, automatically identifies alternative trains and stations, and synthesizes plain-language trade-offs using local <strong className="text-purple-300">GPT4All</strong> and automated <strong className="text-emerald-300">SMS + Email</strong> alerts.
          </p>
          <div className="mt-4 inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-cyan-950/60 border border-cyan-800/60 text-xs font-mono text-cyan-300">
            <span>RAILRADAR API ↓ NORMALIZATION ↓ EVENT ENGINE ↓ JOURNEY STATE ↓ IMPACT ↓ ALTERNATIVE ENGINE ↓ DECISION ↓ GPT4ALL ↓ SMS / EMAIL ↓ REACT</span>
          </div>
        </div>
      </div>

      {/* 8-Stage Flow Visualization */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-6 flex items-center space-x-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>Real-Time Intelligence Pipeline</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-8 gap-3">
          {/* Stage 1 */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 mb-1">Source Layer</div>
              <div className="font-bold text-xs text-white mb-1">1. RailRadar API</div>
              <p className="text-[11px] text-slate-400">Live endpoint: GET /v1/trains/{'{number}'}/live</p>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              Bearer Auth
            </div>
          </div>

          {/* Stage 2 */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 mb-1">Adapter</div>
              <div className="font-bold text-xs text-white mb-1">2. Data Normalizer</div>
              <p className="text-[11px] text-slate-400">Normalizes RailRadar delays, stations, schedules</p>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              railway_api.py
            </div>
          </div>

          {/* Stage 3 */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 mb-1">Live Monitor</div>
              <div className="font-bold text-xs text-white mb-1">3. Status Poller</div>
              <p className="text-[11px] text-slate-400">30s interval poller detecting running state deltas</p>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              live_update_service
            </div>
          </div>

          {/* Stage 4 */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 mb-1">State Engine</div>
              <div className="font-bold text-xs text-white mb-1">4. Journey State</div>
              <p className="text-[11px] text-slate-400">Computes updated arrival & buffer = dep - arr</p>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              journey_state.py
            </div>
          </div>

          {/* Stage 5 */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-amber-400 mb-1">Deterministic</div>
              <div className="font-bold text-xs text-white mb-1">5. Impact Engine</div>
              <p className="text-[11px] text-slate-400">Evaluates buffer vs 30m safety threshold</p>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              impact_engine.py
            </div>
          </div>

          {/* Stage 6 */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 mb-1">Routing</div>
              <div className="font-bold text-xs text-white mb-1">6. Alternative Engine</div>
              <p className="text-[11px] text-slate-400">Same-station + nearby station options & ETA</p>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              alternative_engine
            </div>
          </div>

          {/* Stage 7 */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-purple-400 mb-1">Local LLM</div>
              <div className="font-bold text-xs text-white mb-1">7. GPT4All Agent</div>
              <p className="text-[11px] text-slate-400">Explains trade-offs (RAC vs CNF, station transfer)</p>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              gpt4all_agent.py
            </div>
          </div>

          {/* Stage 8 */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 mb-1">Dispatch</div>
              <div className="font-bold text-xs text-white mb-1">8. SMS & Email</div>
              <p className="text-[11px] text-slate-400">Automated notification when delay ≥ 30m</p>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500">
              notification_service
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Section: Core Architectural Principles & Live System Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Core Principles */}
        <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <Shield className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Guaranteed Architectural Principles</h3>
          </div>

          <div className="space-y-3.5 text-xs text-slate-300">
            <div className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-white">Deterministic Decision Making:</strong> The Decision and Impact engines
                are 100% deterministic code. Feasibility is computed strictly before GPT4All receives the structured matrix.
              </div>
            </div>

            <div className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-white">Zero-Hallucination GPT4All Assistant:</strong> GPT4All is strictly an explanation and comparison layer.
                It is forbidden from fabricating train numbers, timings, station names, or fares. If railway data is missing, it explicitly reports "Not provided by RailRadar".
              </div>
            </div>

            <div className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-white">Automated Alternative Discovery:</strong> The passenger does NOT need to press "Find Alternatives".
                When RailRadar reports a meaningful delay, RailMind automatically identifies the affected journey, recalculates downstream impacts, searches alternative trains and junction stations, and dispatches SMS/Email alerts.
              </div>
            </div>

            <div className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-white">Relational SQLite Persistence:</strong> 14 normalized tables
                manage journeys, legs, trains, bookings, passenger contacts, notifications, schedules, and refresh logs.
              </div>
            </div>
          </div>
        </div>

        {/* Live System Diagnostics */}
        <div className="lg:col-span-5 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <Server className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white">Live System Diagnostics</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Database Layer:</span>
              <span className="font-mono font-bold text-emerald-400">
                {systemHealth?.database || 'SQLite3 (railway.db)'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Data Source:</span>
              <span className="font-mono font-bold text-cyan-400">
                {systemHealth?.data_adapter_mode || 'RailRadar Live API'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Local LLM:</span>
              <span className="font-mono font-bold text-purple-400">
                {systemHealth?.strands_status || 'GPT4All (Local LLM)'}
              </span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Tracked Active Journeys:</span>
              <span className="font-mono font-bold text-white">
                {systemHealth?.active_journeys_count || 1} Active PNRs
              </span>
            </div>

            <div className="flex justify-between py-1.5">
              <span className="text-slate-400">Railway Events Logged:</span>
              <span className="font-mono font-bold text-white">
                {systemHealth?.events_count || 0} in SQLite
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
