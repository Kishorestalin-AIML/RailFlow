import React from 'react';
import { AlertCircle, Clock, ShieldAlert, CheckCircle2, ArrowRightCircle, Gauge } from 'lucide-react';
import { ImpactResult } from '../types';

interface ImpactPanelProps {
  impact: ImpactResult;
}

export const ImpactPanel: React.FC<ImpactPanelProps> = ({ impact }) => {
  const isMissed = impact.impact_type === 'MISSED_CONNECTION';
  const isRisk = impact.impact_type === 'CONNECTION_RISK';
  const isSafe = impact.severity === 'LOW';

  const severityBadgeClass = isMissed
    ? 'bg-rose-600 text-white'
    : isRisk
    ? 'bg-amber-600 text-white'
    : 'bg-emerald-600 text-white';

  const containerBorderClass = isMissed
    ? 'border-rose-300 bg-rose-50/20'
    : isRisk
    ? 'border-amber-300 bg-amber-50/20'
    : 'border-emerald-200 bg-emerald-50/20';

  return (
    <div className={`rounded-xl border shadow-sm p-6 mb-6 transition-all ${containerBorderClass} bg-white`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-2">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-lg ${
            isMissed ? 'bg-rose-100 text-rose-700' : isRisk ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
          }`}>
            {isMissed ? (
              <ShieldAlert className="w-6 h-6" />
            ) : isRisk ? (
              <AlertCircle className="w-6 h-6" />
            ) : (
              <CheckCircle2 className="w-6 h-6" />
            )}
          </div>
          <div>
            <span className="text-xs uppercase font-bold tracking-wider text-slate-500">
              Impact Analysis Engine
            </span>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              JOURNEY IMPACT ASSESSMENT
            </h2>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${severityBadgeClass}`}>
            {impact.impact_type.replace(/_/g, ' ')}
          </span>
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
            SEVERITY: {impact.severity}
          </span>
        </div>
      </div>

      {/* Dominant Metric Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
        {/* Train Delay Metric */}
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-[11px] font-semibold text-slate-500 uppercase">Affected Train</div>
          <div className="text-base font-bold font-mono text-slate-900 mt-0.5">
            {impact.affected_train}
          </div>
          <div className="text-xs font-bold mt-1 text-amber-700">
            {impact.delay_minutes > 0 ? `+${impact.delay_minutes} min delay` : 'On Time'}
          </div>
        </div>

        {/* Expected Arrival */}
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-[11px] font-semibold text-slate-500 uppercase">Expected Arrival</div>
          <div className="text-base font-bold font-mono text-slate-900 mt-0.5">
            {impact.expected_arrival || 'N/A'}
          </div>
          <div className="text-xs text-slate-500 mt-1">Transfer Station</div>
        </div>

        {/* Connection Departure */}
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-[11px] font-semibold text-slate-500 uppercase">Connecting Dep.</div>
          <div className="text-base font-bold font-mono text-slate-900 mt-0.5">
            {impact.connection_departure || 'N/A'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            Train {impact.connection_train || 'N/A'}
          </div>
        </div>

        {/* Remaining Buffer */}
        <div className={`p-3.5 rounded-lg border ${
          isMissed
            ? 'bg-rose-50 border-rose-200 text-rose-900'
            : isRisk
            ? 'bg-amber-50 border-amber-200 text-amber-900'
            : 'bg-emerald-50 border-emerald-200 text-emerald-900'
        }`}>
          <div className="text-[11px] font-semibold uppercase">Remaining Buffer</div>
          <div className="text-xl font-black font-mono mt-0.5">
            {impact.remaining_buffer_minutes !== null && impact.remaining_buffer_minutes !== undefined
              ? `${impact.remaining_buffer_minutes} min`
              : 'N/A'}
          </div>
          <div className="text-xs font-medium mt-1">
            {isMissed ? 'Transfer Elapsed' : isRisk ? 'Safety Window Breached' : 'Adequate Time'}
          </div>
        </div>

        {/* Required Safe Buffer */}
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
          <div className="text-[11px] font-semibold text-slate-500 uppercase">Required Buffer</div>
          <div className="text-base font-bold font-mono text-slate-900 mt-0.5">
            {impact.required_buffer_minutes} min
          </div>
          <div className="text-xs text-slate-500 mt-1">Safety Policy Threshold</div>
        </div>
      </div>

      {/* Summary Narrative Banner */}
      <div className={`p-3.5 rounded-lg border flex items-start space-x-3 ${
        isMissed
          ? 'bg-rose-100/60 border-rose-200 text-rose-900'
          : isRisk
          ? 'bg-amber-100/60 border-amber-200 text-amber-900'
          : 'bg-emerald-100/60 border-emerald-200 text-emerald-900'
      }`}>
        <Gauge className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div className="text-xs font-medium leading-relaxed">
          <span className="font-bold mr-1">Deterministic Assessment:</span>
          {impact.status_summary}
        </div>
      </div>
    </div>
  );
};
