import React, { useState, useEffect } from 'react';
import { Activity, Zap, RotateCcw, AlertTriangle, CheckCircle, Database, Server, ArrowRight, Play, Layers } from 'lucide-react';
import { simulateDelay, simulateCancellation, simulateReset, injectCustomEvent, fetchEvents } from '../services/api';
import { RailwayEventItem } from '../types';

interface SimulationConsoleProps {
  onEventInjected: () => void;
}

export const SimulationConsole: React.FC<SimulationConsoleProps> = ({ onEventInjected }) => {
  const [selectedTrain, setSelectedTrain] = useState('12601');
  const [selectedEventType, setSelectedEventType] = useState('TRAIN_DELAY');
  const [delayMinutes, setDelayMinutes] = useState(75);
  const [customReason, setCustomReason] = useState('Interlocking signal delay near Katpadi');
  const [executing, setExecuting] = useState(false);
  const [activeStage, setActiveStage] = useState<number | null>(null);
  const [recentEvents, setRecentEvents] = useState<RailwayEventItem[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadRecentEvents = async () => {
    try {
      const data = await fetchEvents(10);
      setRecentEvents(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadRecentEvents();
  }, []);

  // Simulate pipeline visualization
  const runPipelineAnimation = async () => {
    for (let stage = 1; stage <= 6; stage++) {
      setActiveStage(stage);
      await new Promise((resolve) => setTimeout(resolve, 200));
    }
    setTimeout(() => setActiveStage(null), 1500);
  };

  const handleQuick75MinDelay = async () => {
    setExecuting(true);
    setStatusMessage('Injecting +75 min delay on Train 12601...');
    try {
      runPipelineAnimation();
      await simulateDelay('12601', 75);
      setStatusMessage('✓ +75 min delay processed. Journey recalculated: buffer reduced to 10m (At Risk).');
      await loadRecentEvents();
      onEventInjected();
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const handleQuickCancellation = async () => {
    setExecuting(true);
    setStatusMessage('Injecting train cancellation event...');
    try {
      runPipelineAnimation();
      await simulateCancellation('12601');
      setStatusMessage('✓ Train 12601 cancellation event processed.');
      await loadRecentEvents();
      onEventInjected();
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const handleReset = async () => {
    setExecuting(true);
    setStatusMessage('Resetting demo journey to normal safe baseline...');
    try {
      await simulateReset();
      setStatusMessage('✓ Journey reset: 0 delay, 50m safe buffer restored.');
      await loadRecentEvents();
      onEventInjected();
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const handleCustomEventSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setExecuting(true);
    setStatusMessage(`Injecting ${selectedEventType} on Train ${selectedTrain}...`);
    try {
      runPipelineAnimation();
      await injectCustomEvent({
        event_type: selectedEventType,
        train_id: selectedTrain,
        delay_minutes: selectedEventType === 'TRAIN_DELAY' || selectedEventType === 'ETA_CHANGED' ? delayMinutes : 0,
        source: 'simulation_console',
        details: { reason: customReason }
      });
      setStatusMessage(`✓ ${selectedEventType} successfully processed through backend pipeline.`);
      await loadRecentEvents();
      onEventInjected();
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const pipelineStages = [
    { num: 1, name: 'Simulation Event', desc: 'Normalized Payload' },
    { num: 2, name: 'Event Engine', desc: 'Validates & Persists' },
    { num: 3, name: 'Journey State', desc: 'Recalculates Legs' },
    { num: 4, name: 'Impact Engine', desc: 'Evaluates Transfer Buffer' },
    { num: 5, name: 'Decision Engine', desc: 'Deterministic Rules' },
    { num: 6, name: 'Strands & UI', desc: 'Passenger Advice' }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header Banner */}
      <div className="bg-railnavy-900 rounded-xl p-6 mb-6 text-white shadow-md border border-railnavy-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <Activity className="w-6 h-6 text-amber-400" />
              <h1 className="text-xl font-bold tracking-tight">Railway Operational Simulation Console</h1>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                Hackathon Demo Centerpiece
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl">
              Inject real railway disruptions into the intelligence layer. Events travel strictly through the
              full backend pipeline: SQLite ➔ Event Engine ➔ Journey State ➔ Impact ➔ Decision ➔ Recommendation ➔ Strands.
            </p>
          </div>

          {/* Preset Scenario Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleQuick75MinDelay}
              disabled={executing}
              className="px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider bg-amber-500 hover:bg-amber-600 text-slate-950 shadow-sm transition-all flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
            >
              <Zap className="w-4 h-4 text-slate-950" />
              <span>⚡ Inject +75m Delay</span>
            </button>

            <button
              onClick={handleQuickCancellation}
              disabled={executing}
              className="px-3 py-2 rounded-lg text-xs font-bold uppercase tracking-wider bg-rose-600 hover:bg-rose-700 text-white transition-all flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Cancel Train</span>
            </button>

            <button
              onClick={handleReset}
              disabled={executing}
              className="px-3 py-2 rounded-lg text-xs font-bold uppercase tracking-wider bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset Baseline</span>
            </button>
          </div>
        </div>

        {/* Dynamic Pipeline Progress Bar */}
        <div className="mt-6 pt-5 border-t border-railnavy-800">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
            <span>Real-Time Pipeline Execution:</span>
            {statusMessage && (
              <span className="text-xs font-medium text-cyan-300 font-mono">{statusMessage}</span>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {pipelineStages.map((stage) => {
              const isActive = activeStage === stage.num;
              const isPast = activeStage !== null && activeStage > stage.num;

              return (
                <div
                  key={stage.num}
                  className={`p-2.5 rounded-lg border transition-all ${
                    isActive
                      ? 'bg-cyan-950/80 border-cyan-400 ring-2 ring-cyan-400 text-white'
                      : isPast
                      ? 'bg-railnavy-800/80 border-emerald-500 text-emerald-300'
                      : 'bg-railnavy-800/40 border-railnavy-700 text-slate-400'
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] font-bold mb-0.5">
                    <span>{stage.num}. {stage.name}</span>
                    {isPast && <CheckCircle className="w-3 h-3 text-emerald-400" />}
                  </div>
                  <div className="text-[10px] text-slate-400 truncate">{stage.desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Two Column Layout: Custom Injection Form & Live Audit Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Custom Event Builder */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-xs p-6">
          <div className="flex items-center space-x-2 pb-3 mb-4 border-b border-slate-100">
            <Layers className="w-5 h-5 text-railblue-700" />
            <h2 className="text-base font-bold text-slate-900">Custom Event Injector</h2>
          </div>

          <form onSubmit={handleCustomEventSubmit} className="space-y-4">
            {/* Train Selector */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                Target Train Number
              </label>
              <select
                value={selectedTrain}
                onChange={(e) => setSelectedTrain(e.target.value)}
                className="w-full text-xs font-bold px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-railblue-500 bg-white"
              >
                <option value="12601">12601 - Cheran SF Express (CBE → MAS) [Leg 1]</option>
                <option value="12615">12615 - Grand Trunk Express (MAS → NDLS) [Leg 2]</option>
                <option value="12676">12676 - Kovai Express (CBE → MAS)</option>
                <option value="22625">22625 - Double Decker Express (CBE → MAS)</option>
                <option value="12621">12621 - Tamil Nadu Express (MAS → NDLS)</option>
              </select>
            </div>

            {/* Event Type */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                Railway Event Type
              </label>
              <select
                value={selectedEventType}
                onChange={(e) => setSelectedEventType(e.target.value)}
                className="w-full text-xs font-bold px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-railblue-500 bg-white"
              >
                <option value="TRAIN_DELAY">TRAIN_DELAY (Increases Arrival Delay)</option>
                <option value="TRAIN_CANCELLED">TRAIN_CANCELLED (Service Disruption)</option>
                <option value="ETA_CHANGED">ETA_CHANGED (Dynamic Running Update)</option>
                <option value="BOOKING_STATUS_CHANGED">BOOKING_STATUS_CHANGED (RAC/WL Update)</option>
                <option value="RAC_MOVEMENT">RAC_MOVEMENT (Coach Berthing Upgrade)</option>
                <option value="AVAILABILITY_CHANGED">AVAILABILITY_CHANGED (Quota Release)</option>
              </select>
            </div>

            {/* Delay Slider */}
            {(selectedEventType === 'TRAIN_DELAY' || selectedEventType === 'ETA_CHANGED') && (
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Delay Duration
                  </label>
                  <span className="font-mono font-bold text-sm text-amber-700">
                    +{delayMinutes} minutes
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="180"
                  step="5"
                  value={delayMinutes}
                  onChange={(e) => setDelayMinutes(Number(e.target.value))}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                  <span>0m (On Time)</span>
                  <span>30m (Threshold)</span>
                  <span>75m (Demo)</span>
                  <span>180m</span>
                </div>
              </div>
            )}

            {/* Operational Reason */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                Operational Reason
              </label>
              <input
                type="text"
                value={customReason}
                onChange={(e) => setCustomReason(e.target.value)}
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-railblue-500 bg-white"
              />
            </div>

            <button
              type="submit"
              disabled={executing}
              className="w-full py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-railnavy-900 hover:bg-railnavy-800 text-white transition-colors flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Inject Event Into Pipeline</span>
            </button>
          </form>
        </div>

        {/* Live SQLite Event Feed & Audit Log */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs p-6">
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <Database className="w-5 h-5 text-railblue-700" />
              <h2 className="text-base font-bold text-slate-900">SQLite Database Event Audit</h2>
            </div>
            <span className="text-xs text-slate-500 font-mono">railway.db (events table)</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-bold border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2.5">Event ID</th>
                  <th className="px-3 py-2.5">Type</th>
                  <th className="px-3 py-2.5">Train</th>
                  <th className="px-3 py-2.5">Timestamp</th>
                  <th className="px-3 py-2.5">Payload</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentEvents.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-6 text-center text-slate-400">
                      No events recorded in database yet.
                    </td>
                  </tr>
                ) : (
                  recentEvents.map((evt) => (
                    <tr key={evt.event_id} className="hover:bg-slate-50 font-mono">
                      <td className="px-3 py-2 font-bold text-slate-700">{evt.event_id}</td>
                      <td className="px-3 py-2">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          evt.event_type.includes('DELAY')
                            ? 'bg-amber-100 text-amber-800'
                            : evt.event_type.includes('CANCEL')
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {evt.event_type}
                        </span>
                      </td>
                      <td className="px-3 py-2 font-semibold text-slate-900">{evt.train_id}</td>
                      <td className="px-3 py-2 text-slate-500 text-[11px]">{evt.timestamp}</td>
                      <td className="px-3 py-2 text-[10px] text-slate-600 truncate max-w-[140px]" title={JSON.stringify(evt.payload)}>
                        {JSON.stringify(evt.payload)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
