import React, { useState } from 'react';
import { Train, Clock, ArrowRight, ShieldCheck, AlertCircle, MapPin, Check, ExternalLink } from 'lucide-react';
import { AlternativeComparisonMatrix, AlternativeOptionItem } from '../types';

interface Props {
  matrix: AlternativeComparisonMatrix | null;
  loading?: boolean;
}

export const AlternativeComparisonTable: React.FC<Props> = ({ matrix, loading }) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [decisionFeedback, setDecisionFeedback] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-2xl animate-pulse">
        <Clock className="w-8 h-8 text-cyan-400 mx-auto mb-3 animate-spin" />
        <div className="text-slate-300 font-medium">Calculating feasible alternative trains & stations...</div>
        <div className="text-xs text-slate-500 mt-1">Evaluating live RailRadar timings, transfer safety buffers, and availability</div>
      </div>
    );
  }

  if (!matrix || !matrix.alternatives || matrix.alternatives.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/40 border border-slate-800/80 rounded-2xl">
        <ShieldCheck className="w-10 h-10 text-emerald-400 mx-auto mb-3 opacity-80" />
        <h3 className="text-base font-semibold text-white">No Alternative Trains Needed</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
          Your current connection buffer remains safe according to real-time RailRadar monitoring. Alternatives will automatically appear if a delay compromises your journey.
        </p>
      </div>
    );
  }

  const { current_journey, alternatives } = matrix;

  const handleSelectOption = (opt: AlternativeOptionItem) => {
    setSelectedOption(opt.option_letter || opt.train_number);
    setDecisionFeedback(
      `Option ${opt.option_letter || 'Alt'} selected (${opt.train_name}). Passenger retains full control — open IRCTC or reservation window to secure this connection.`
    );
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="p-5 border-b border-slate-800 bg-slate-950/40 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-white">Alternative Ways to Reach Your Destination</h3>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
              {alternatives.length} Feasible Options
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Factual time and availability comparison based on live RailRadar tracking. Ranked by arrival time and connection feasibility.
          </p>
        </div>
      </div>

      {decisionFeedback && (
        <div className="mx-5 mt-4 p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-300 flex items-center justify-between animate-fade-in">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-400" />
            <span>{decisionFeedback}</span>
          </div>
          <button
            onClick={() => setDecisionFeedback(null)}
            className="text-slate-400 hover:text-white text-xs font-medium"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold tracking-wider uppercase">
              <th className="py-3 px-4">Option</th>
              <th className="py-3 px-4">Train</th>
              <th className="py-3 px-4">Departure Station</th>
              <th className="py-3 px-4">Departure</th>
              <th className="py-3 px-4 text-cyan-300">Destination Arrival</th>
              <th className="py-3 px-4">Transfer</th>
              <th className="py-3 px-4">Availability</th>
              <th className="py-3 px-4">Fare</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {/* Current Planned Journey Row */}
            <tr className="bg-slate-950/20 text-slate-300 font-medium">
              <td className="py-3.5 px-4">
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Current
                </span>
              </td>
              <td className="py-3.5 px-4">
                <div className="font-semibold text-white">{current_journey.train}</div>
                <div className="text-[11px] text-slate-500">{current_journey.train_name}</div>
              </td>
              <td className="py-3.5 px-4 text-slate-300">{current_journey.station}</td>
              <td className="py-3.5 px-4 font-mono text-slate-300">{current_journey.departure}</td>
              <td className="py-3.5 px-4 font-mono font-semibold text-slate-200">
                {current_journey.expected_destination_arrival}
              </td>
              <td className="py-3.5 px-4 text-slate-400">Direct / Scheduled</td>
              <td className="py-3.5 px-4">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  {current_journey.availability}
                </span>
              </td>
              <td className="py-3.5 px-4 font-mono text-slate-300">{current_journey.formatted_fare}</td>
              <td className="py-3.5 px-4 text-right">
                <span className="text-[11px] text-slate-500">Scheduled Booking</span>
              </td>
            </tr>

            {/* Alternative Candidate Rows */}
            {alternatives.map((alt, idx) => {
              const isSelected = selectedOption === (alt.option_letter || alt.train_number);
              const isAlternativeStation = alt.option_type === 'ALTERNATIVE_STATION';

              return (
                <tr
                  key={idx}
                  className={`transition-colors hover:bg-slate-800/40 ${
                    isSelected ? 'bg-cyan-950/20 border-l-2 border-cyan-400' : ''
                  }`}
                >
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-cyan-600/20 text-cyan-300 font-bold border border-cyan-500/30">
                      {alt.option_letter || idx + 1}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-white">{alt.train_number}</div>
                    <div className="text-[11px] text-slate-400">{alt.train_name}</div>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1.5 text-slate-200 font-medium">
                      {isAlternativeStation && <MapPin className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                      <span>{alt.station_name}</span>
                    </div>
                    {isAlternativeStation && (
                      <div className="text-[10px] text-amber-400/80">Nearby junction</div>
                    )}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-200">{alt.departure_time}</td>
                  <td className="py-3.5 px-4">
                    <div className="font-mono font-bold text-cyan-400 text-sm">
                      {alt.expected_destination_arrival}
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    {alt.transfer_time_minutes > 0 ? (
                      <span className="text-amber-300 font-medium">{alt.transfer_time_minutes} min transfer</span>
                    ) : (
                      <span className="text-slate-400">Same station ({alt.waiting_time_minutes}m buffer)</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${
                        alt.availability_status === 'CONFIRMED'
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                          : alt.availability_status === 'RAC'
                          ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                          : 'bg-slate-800 text-slate-300 border-slate-700'
                      }`}
                    >
                      {alt.availability}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-200">{alt.formatted_fare}</td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => handleSelectOption(alt)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                        isSelected
                          ? 'bg-cyan-500 text-slate-950 font-bold shadow-lg shadow-cyan-500/30'
                          : 'bg-slate-800 hover:bg-slate-700 text-cyan-300 hover:text-white border border-slate-700'
                      }`}
                    >
                      {isSelected ? 'Chosen' : 'Select'}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer / Transparency Disclaimer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-500">
        <div className="flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 text-slate-400" />
          <span>RailMind provides factual intelligence only. RailMind does NOT automatically book or cancel railway tickets.</span>
        </div>
        <div className="text-slate-400 font-mono">
          Updated with verified RailRadar timetables
        </div>
      </div>
    </div>
  );
};
