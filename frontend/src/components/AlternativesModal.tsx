import React from 'react';
import { X, Train, Clock, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { TrainSearchResult } from '../types';

interface AlternativesModalProps {
  isOpen: boolean;
  onClose: () => void;
  alternatives: TrainSearchResult[];
  transferStation: string;
  expectedArrival: string;
}

export const AlternativesModal: React.FC<AlternativesModalProps> = ({
  isOpen,
  onClose,
  alternatives,
  transferStation,
  expectedArrival
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-railnavy-900 text-white">
          <div className="flex items-center space-x-2.5">
            <Train className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-base font-bold text-white">Alternative Connection Options</h3>
              <p className="text-xs text-slate-300">
                Departing from {transferStation} after estimated arrival ({expectedArrival})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-300 hover:text-white hover:bg-railnavy-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-900 flex items-start space-x-2">
            <ShieldCheck className="w-4 h-4 text-blue-700 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Official Railway Policy:</span> Passengers with connecting PNRs disrupted by train delays exceeding safety buffers can present this itinerary at the Chief Commercial Inspector (CCI) desk or IRCTC portal for priority accommodation or full fare refund.
            </div>
          </div>

          <div className="space-y-3">
            {alternatives.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-6">
                No subsequent services found for the requested route.
              </p>
            ) : (
              alternatives.map((train) => (
                <div
                  key={train.train_number}
                  className="p-4 rounded-lg border border-slate-200 bg-white hover:border-railblue-300 hover:shadow-xs transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-railnavy-900 text-white">
                          {train.train_number}
                        </span>
                        <span className="text-sm font-bold text-slate-900">{train.train_name}</span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {train.running_status}
                        </span>
                      </div>

                      <div className="text-xs text-slate-600 mt-2 flex items-center space-x-4">
                        <span>
                          Departs: <strong className="text-slate-900">{train.departure_time}</strong>
                        </span>
                        <span>
                          Arrives: <strong className="text-slate-900">{train.arrival_time}</strong>
                        </span>
                        <span>Duration: {train.duration_formatted}</span>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-1.5 sm:self-center">
                      {train.availabilities?.map((av) => (
                        <div
                          key={av.class_type}
                          className="px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-[11px] text-center"
                        >
                          <div className="font-bold text-slate-800">{av.class_type}</div>
                          <div className={`font-semibold ${
                            av.status === 'AVAILABLE' ? 'text-emerald-700' : 'text-amber-700'
                          }`}>
                            {av.status === 'AVAILABLE' ? `AVL ${av.seats_available}` : av.status}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Note: RailMind does not book tickets without passenger confirmation.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider bg-railnavy-900 hover:bg-railnavy-800 text-white transition-colors cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
