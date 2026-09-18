import React, { useState } from 'react';
import { Compass, CheckCircle, AlertTriangle, ArrowRight, Bell, ShieldQuestion, ExternalLink } from 'lucide-react';
import { DecisionResult, RecommendationResult } from '../types';

interface DecisionPanelProps {
  decision: DecisionResult;
  recommendation?: RecommendationResult;
  onReviewAlternatives: () => void;
  onContinueMonitoring: () => void;
  onSetAlert: () => void;
}

export const DecisionPanel: React.FC<DecisionPanelProps> = ({
  decision,
  recommendation,
  onReviewAlternatives,
  onContinueMonitoring,
  onSetAlert
}) => {
  const [activeAlertSet, setActiveAlertSet] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);

  const handleAlertClick = () => {
    setActiveAlertSet(true);
    onSetAlert();
  };

  const handleContinueClick = () => {
    setAcknowledged(true);
    onContinueMonitoring();
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-railblue-50 text-railblue-700">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs uppercase font-bold tracking-wider text-railblue-700">Deterministic Engine</span>
            <h2 className="text-lg font-bold text-slate-900">DECISION SUPPORT & ACTION PLAN</h2>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
            Rule-Based Deterministic Execution
          </span>
        </div>
      </div>

      {/* Decision Summary Grid */}
      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 mb-5 space-y-2.5">
        <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4">
          <span className="text-xs font-bold text-slate-500 uppercase min-w-[140px]">Current situation:</span>
          <span className={`text-sm font-bold uppercase ${
            decision.situation_status === 'MISSED'
              ? 'text-rose-700'
              : decision.situation_status === 'AT_RISK'
              ? 'text-amber-700'
              : 'text-emerald-700'
          }`}>
            {decision.situation_status === 'AT_RISK' ? 'Connection at risk' : decision.situation_status}
          </span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4">
          <span className="text-xs font-bold text-slate-500 uppercase min-w-[140px]">System assessment:</span>
          <span className="text-sm font-semibold text-slate-800">
            {decision.system_assessment}
          </span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4">
          <span className="text-xs font-bold text-slate-500 uppercase min-w-[140px]">Reason:</span>
          <span className="text-xs text-slate-600 leading-relaxed">
            {decision.reason}
          </span>
        </div>
      </div>

      {/* Structured Feasible Options */}
      {recommendation?.options && recommendation.options.length > 0 && (
        <div className="mb-5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2.5">
            Evaluated Feasible Options
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {recommendation.options.map((opt, i) => (
              <div key={i} className="p-3.5 rounded-lg border border-slate-200 bg-white hover:border-railblue-300 transition-colors">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-slate-900">{opt.title}</span>
                  {opt.tag && (
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-railblue-50 text-railblue-700 border border-railblue-200">
                      {opt.tag}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{opt.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="pt-2 border-t border-slate-100">
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onReviewAlternatives}
            className="px-4 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-railblue-700 hover:bg-railblue-800 text-white shadow-xs transition-colors flex items-center space-x-2 cursor-pointer"
          >
            <span>Review Alternative Connections</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleContinueClick}
            className={`px-4 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider border transition-colors flex items-center space-x-2 cursor-pointer ${
              acknowledged
                ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
            }`}
          >
            <CheckCircle className="w-3.5 h-3.5" />
            <span>{acknowledged ? 'Monitoring Active' : 'Continue Monitoring'}</span>
          </button>

          <button
            onClick={handleAlertClick}
            className={`px-4 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider border transition-colors flex items-center space-x-2 cursor-pointer ${
              activeAlertSet
                ? 'bg-railblue-50 text-railblue-700 border-railblue-300'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
            }`}
          >
            <Bell className="w-3.5 h-3.5 text-slate-500" />
            <span>{activeAlertSet ? '10-Min Proximity Alert Set' : 'Set Delay Alert'}</span>
          </button>
        </div>

        {acknowledged && (
          <p className="text-xs text-emerald-700 font-medium mt-2">
            ✓ Passenger confirmed monitoring. RailMind background engines will continuously poll running reports.
          </p>
        )}
      </div>
    </div>
  );
};
