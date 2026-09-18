import React from 'react';
import { Train, Clock, ArrowRight, ShieldCheck, Ticket } from 'lucide-react';
import { RecommendationResult } from '../types';

interface AlternativeTrainsPanelProps {
  recommendation?: RecommendationResult;
  transferStation: string;
  expectedArrival: string;
  onOpenModal: () => void;
}

export const AlternativeTrainsPanel: React.FC<AlternativeTrainsPanelProps> = ({
  recommendation,
  transferStation,
  expectedArrival,
  onOpenModal
}) => {
  // Extract alternatives embedded in recommendation options
  const optionWithAlts = recommendation?.options?.find((o: any) => o.alternatives && o.alternatives.length > 0);
  const alternatives = (optionWithAlts as any)?.alternatives || [];

  if (alternatives.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-4 border-b border-slate-100 gap-2">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-lg bg-railblue-50 text-railblue-700">
            <Train className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Alternative Connection Options</h3>
            <p className="text-xs text-slate-500">
              Viable subsequent departures from {transferStation} after expected arrival ({expectedArrival})
            </p>
          </div>
        </div>

        <button
          onClick={onOpenModal}
          className="text-xs font-semibold text-railblue-700 hover:text-railblue-800 flex items-center space-x-1 cursor-pointer"
        >
          <span>View All Alternatives</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {alternatives.slice(0, 2).map((alt: any) => (
          <div
            key={alt.train_number}
            className="p-4 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-railblue-300 transition-all"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-railnavy-900 text-white">
                  {alt.train_number}
                </span>
                <span className="text-xs font-bold text-slate-900">{alt.train_name}</span>
              </div>
              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                {alt.feasibility_tag}
              </span>
            </div>

            <div className="text-xs text-slate-600 mb-3 flex items-center space-x-4">
              <span>
                Departs: <strong className="text-slate-900">{alt.departure_time}</strong>
              </span>
              <span>
                Arrives: <strong className="text-slate-900">{alt.arrival_time}</strong>
              </span>
              <span>Transfer Window: <strong>{alt.transfer_window_minutes}m</strong></span>
            </div>

            {/* Availability & Fare Badges */}
            <div className="pt-2 border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center space-x-2">
                <span className="text-[11px] text-slate-500 font-medium">Availability:</span>
                <span className="text-xs font-bold text-emerald-700">
                  {alt.availabilities?.[0]?.status === 'AVAILABLE'
                    ? `AVL (${alt.availabilities[0].seats_available} seats)`
                    : alt.availabilities?.[0]?.status || 'Not provided'}
                </span>
              </div>

              <div className="flex items-center space-x-1">
                <span className="text-[11px] text-slate-500 font-medium">Fare:</span>
                <span className="text-xs font-mono font-bold text-slate-900">
                  {alt.availabilities?.[0]?.fare_formatted || 'Not provided'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span>RailMind provides decision intelligence. Tickets are not automatically modified.</span>
        <button
          onClick={onOpenModal}
          className="font-bold text-railblue-700 hover:underline cursor-pointer"
        >
          Inspect Alternatives & Booking Details
        </button>
      </div>
    </div>
  );
};
