import React from 'react';
import { Clock, AlertTriangle, CheckCircle2, ArrowRight, ShieldAlert, Timer } from 'lucide-react';
import { JourneyDetail } from '../types';

interface JourneyTimelineProps {
  journey: JourneyDetail;
}

export const JourneyTimeline: React.FC<JourneyTimelineProps> = ({ journey }) => {
  const legs = journey.legs;
  const buffer = journey.connection_buffer_minutes ?? 50;
  const isBufferAtRisk = buffer < journey.minimum_safe_buffer_minutes && buffer > 0;
  const isBufferMissed = buffer <= 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-6 border-b border-slate-100">
        <div>
          <span className="text-xs uppercase font-bold tracking-wider text-railblue-700">Journey Itinerary</span>
          <h2 className="text-lg font-bold text-slate-900 mt-0.5">
            {journey.source_station.name} ({journey.source_station.code}) → {journey.destination_station.name} ({journey.destination_station.code})
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Travel Date: <span className="font-semibold text-slate-700">{journey.journey_date}</span> • PNR: <span className="font-mono font-semibold text-railblue-800">{journey.pnr}</span>
          </p>
        </div>

        <div className="mt-3 sm:mt-0 flex items-center space-x-2">
          {journey.journey_status === 'SAFE' && (
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>ON SCHEDULE • SAFE BUFFER</span>
            </span>
          )}
          {journey.journey_status === 'CONNECTION_AT_RISK' && (
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
              <span>CONNECTION AT RISK ({buffer}m remaining)</span>
            </span>
          )}
          {journey.journey_status === 'MISSED' && (
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-300">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
              <span>CONNECTION MISSED</span>
            </span>
          )}
        </div>
      </div>

      {/* Visual Multi-leg Timeline */}
      <div className="space-y-6">
        {legs.map((leg, idx) => {
          const isDelayed = leg.delay_arrival_min > 0;
          const isCancelled = leg.status === 'CANCELLED';

          return (
            <React.Fragment key={leg.leg_order}>
              {/* Leg Card */}
              <div className={`p-4 rounded-lg border transition-all ${
                isDelayed
                  ? 'bg-amber-50/40 border-amber-200'
                  : isCancelled
                  ? 'bg-rose-50/50 border-rose-200'
                  : 'bg-slate-50 border-slate-200'
              }`}>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Origin */}
                  <div className="flex-1">
                    <div className="flex items-baseline space-x-2">
                      <span className="text-xl font-bold font-mono text-slate-900">{leg.from_station.code}</span>
                      <span className="text-sm font-medium text-slate-700">{leg.from_station.name}</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Departure: <span className="font-semibold text-slate-800">{leg.scheduled_departure}</span>
                    </div>
                  </div>

                  {/* Train Service Middle Pill */}
                  <div className="flex-1 text-center py-2 px-4 rounded-md bg-white border border-slate-200 shadow-2xs">
                    <div className="flex items-center justify-center space-x-2">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-railnavy-900 text-white">
                        {leg.train_number}
                      </span>
                      <span className="text-xs font-semibold text-slate-800">{leg.train_name}</span>
                    </div>

                    <div className="mt-1 flex items-center justify-center space-x-2 text-[11px]">
                      {isDelayed ? (
                        <span className="font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
                          +{leg.delay_arrival_min} min delay
                        </span>
                      ) : (
                        <span className="text-emerald-700 font-medium">On Schedule</span>
                      )}
                      <span className="text-slate-400">• Leg {leg.leg_order} of {legs.length}</span>
                    </div>
                  </div>

                  {/* Destination */}
                  <div className="flex-1 md:text-right">
                    <div className="flex md:justify-end items-baseline space-x-2">
                      <span className="text-sm font-medium text-slate-700">{leg.to_station.name}</span>
                      <span className="text-xl font-bold font-mono text-slate-900">{leg.to_station.code}</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Scheduled: <span className="text-slate-600 line-through mr-1">{isDelayed ? leg.scheduled_arrival : ''}</span>
                      <span className={`font-semibold ${isDelayed ? 'text-amber-800 font-bold' : 'text-slate-800'}`}>
                        {leg.actual_arrival || leg.scheduled_arrival}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Inter-leg Transfer Buffer Connector */}
              {idx < legs.length - 1 && (
                <div className="relative pl-6 py-2">
                  <div className="absolute left-10 top-0 bottom-0 w-0.5 bg-slate-300"></div>
                  <div className={`ml-8 p-3 rounded-lg border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 ${
                    isBufferMissed
                      ? 'bg-rose-50 border-rose-300 text-rose-900'
                      : isBufferAtRisk
                      ? 'bg-amber-50 border-amber-300 text-amber-900'
                      : 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                  }`}>
                    <div className="flex items-center space-x-2">
                      <Timer className={`w-4 h-4 ${
                        isBufferMissed ? 'text-rose-600' : isBufferAtRisk ? 'text-amber-600' : 'text-emerald-600'
                      }`} />
                      <span className="text-xs font-semibold uppercase tracking-wider">
                        Interchange Transfer Buffer at {leg.to_station.code}:
                      </span>
                      <span className="font-mono font-bold text-sm">
                        {buffer} minutes
                      </span>
                    </div>

                    <div className="text-xs font-medium">
                      {isBufferMissed ? (
                        <span className="text-rose-700 font-bold">Transfer Window Elapsed (Missed Connection)</span>
                      ) : isBufferAtRisk ? (
                        <span className="text-amber-700 font-bold">
                          Below Safe Minimum ({journey.minimum_safe_buffer_minutes} min threshold)
                        </span>
                      ) : (
                        <span className="text-emerald-700">
                          Healthy buffer (&gt; {journey.minimum_safe_buffer_minutes} min safety margin)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
