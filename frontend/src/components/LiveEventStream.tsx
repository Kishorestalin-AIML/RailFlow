import React from 'react';
import { Activity, Clock, Zap, ArrowRight, CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';

export interface PipelineStep {
  time: string;
  step: string;
  title: string;
  detail: string;
}

interface LiveEventStreamProps {
  steps: PipelineStep[];
}

export const LiveEventStream: React.FC<LiveEventStreamProps> = ({ steps }) => {
  const defaultSteps: PipelineStep[] = [
    {
      time: '14:10:00',
      step: 'BASELINE_ESTABLISHED',
      title: 'Journey Baseline Active',
      detail: 'Train 12601 running on time. Transfer buffer to Train 12615 is 50 minutes (SAFE).'
    }
  ];

  const activeSteps = steps.length > 0 ? steps : defaultSteps;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 mb-6">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-railblue-700" />
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">
              Live Operational Event Stream
            </h3>
            <p className="text-[11px] text-slate-500">
              Real-time audit trail of railway event detection, state recalculation, and decision triggers
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-mono font-medium">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-signal-pulse"></span>
          <span>Event Pipeline Active</span>
        </div>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {activeSteps.map((s, idx) => (
          <div key={idx} className="relative flex items-start space-x-3 group">
            {/* Step dot */}
            <div className={`absolute -left-6 top-1 w-2.5 h-2.5 rounded-full border-2 border-white ring-2 ${
              idx === activeSteps.length - 1 ? 'bg-railblue-600 ring-railblue-300 animate-ping' : 'bg-slate-400 ring-slate-200'
            }`}></div>
            <div className={`absolute -left-6 top-1 w-2.5 h-2.5 rounded-full border-2 border-white ${
              idx === activeSteps.length - 1 ? 'bg-railblue-600' : 'bg-slate-400'
            }`}></div>

            <div className="flex-1 p-3 rounded-lg border border-slate-100 bg-slate-50 hover:bg-white hover:border-slate-300 transition-colors">
              <div className="flex items-center justify-between text-xs mb-1">
                <div className="flex items-center space-x-2">
                  <span className="font-mono font-bold text-slate-500">{s.time}</span>
                  <span className="font-bold text-slate-900">{s.title}</span>
                </div>
                <span className="text-[10px] font-mono font-semibold uppercase px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                  {s.step}
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed font-mono">{s.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
