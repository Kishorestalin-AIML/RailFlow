import React, { useState, useEffect } from 'react';
import { Search, ArrowRightLeft, Clock, Filter, ArrowUpDown, ShieldCheck, Calendar, Train } from 'lucide-react';
import { TrainSearchResult } from '../types';
import { fetchTrainSearch } from '../services/api';

export const TrainSearchPage: React.FC = () => {
  const [origin, setOrigin] = useState('CBE');
  const [destination, setDestination] = useState('MAS');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [trains, setTrains] = useState<TrainSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sorting & Filtering
  const [sortBy, setSortBy] = useState<'departure' | 'duration' | 'availability'>('departure');
  const [selectedClass, setSelectedClass] = useState<string>('ALL');

  const executeSearch = async (fromCode: string, toCode: string) => {
    setLoading(true);
    setError(null);
    try {
      const results = await fetchTrainSearch(fromCode, toCode, date);
      setTrains(results);
    } catch (err: any) {
      console.error(err);
      setError('Unable to fetch train schedules. Please check connection or station codes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeSearch(origin, destination);
  }, []);

  const handleSwapStations = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
    executeSearch(destination, temp);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(origin, destination);
  };

  // Filter & Sort trains
  const filteredTrains = trains.filter((t) => {
    if (selectedClass === 'ALL') return true;
    return t.availabilities?.some((av) => av.class_type === selectedClass);
  });

  filteredTrains.sort((a, b) => {
    if (sortBy === 'departure') {
      return a.departure_time.localeCompare(b.departure_time);
    } else if (sortBy === 'duration') {
      return a.duration_formatted.localeCompare(b.duration_formatted);
    } else if (sortBy === 'availability') {
      const aSeats = a.availabilities?.[0]?.seats_available || 0;
      const bSeats = b.availabilities?.[0]?.seats_available || 0;
      return bSeats - aSeats;
    }
    return 0;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Search Filter Header */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-2">
          <div>
            <h1 className="text-xl font-black text-slate-900 tracking-tight">
              Train Timetable & Seat Availability
            </h1>
            <p className="text-xs text-slate-500">
              Direct integration with Railway API Adapter. Displays normalized train schedules and live seat quotas.
            </p>
          </div>

          {/* Quick Route Buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => {
                setOrigin('CBE');
                setDestination('MAS');
                executeSearch('CBE', 'MAS');
              }}
              className="px-2.5 py-1 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
            >
              Coimbatore → Chennai
            </button>
            <button
              onClick={() => {
                setOrigin('MAS');
                setDestination('NDLS');
                executeSearch('MAS', 'NDLS');
              }}
              className="px-2.5 py-1 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
            >
              Chennai → New Delhi
            </button>
          </div>
        </div>

        <form onSubmit={handleFormSubmit} className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end">
          <div className="sm:col-span-3">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
              From Station
            </label>
            <input
              type="text"
              value={origin}
              onChange={(e) => setOrigin(e.target.value.toUpperCase())}
              placeholder="e.g. CBE"
              className="w-full text-sm font-bold uppercase px-3.5 py-2.5 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-railblue-500 bg-white"
            />
          </div>

          <div className="sm:col-span-1 flex justify-center pb-2">
            <button
              type="button"
              onClick={handleSwapStations}
              className="p-2 rounded-full border border-slate-300 hover:bg-slate-100 text-slate-600 transition-colors"
              title="Swap Stations"
            >
              <ArrowRightLeft className="w-4 h-4" />
            </button>
          </div>

          <div className="sm:col-span-3">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
              To Station
            </label>
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value.toUpperCase())}
              placeholder="e.g. MAS"
              className="w-full text-sm font-bold uppercase px-3.5 py-2.5 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-railblue-500 bg-white"
            />
          </div>

          <div className="sm:col-span-3">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
              Travel Date
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full text-sm px-3.5 py-2.5 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-railblue-500 bg-white"
            />
          </div>

          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-railblue-700 hover:bg-railblue-800 text-white transition-colors flex items-center justify-center space-x-1.5 cursor-pointer disabled:opacity-50"
            >
              <Search className="w-4 h-4" />
              <span>{loading ? 'Searching...' : 'Find Trains'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Sorting & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 bg-white p-3 rounded-lg border border-slate-200">
        <div className="flex items-center space-x-2 text-xs">
          <span className="font-bold text-slate-500 uppercase flex items-center">
            <ArrowUpDown className="w-3.5 h-3.5 mr-1" />
            Sort By:
          </span>
          <button
            onClick={() => setSortBy('departure')}
            className={`px-2.5 py-1 rounded font-medium ${
              sortBy === 'departure' ? 'bg-railnavy-900 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Departure Time
          </button>
          <button
            onClick={() => setSortBy('duration')}
            className={`px-2.5 py-1 rounded font-medium ${
              sortBy === 'duration' ? 'bg-railnavy-900 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Duration
          </button>
          <button
            onClick={() => setSortBy('availability')}
            className={`px-2.5 py-1 rounded font-medium ${
              sortBy === 'availability' ? 'bg-railnavy-900 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Seat Availability
          </button>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="font-bold text-slate-500 uppercase flex items-center">
            <Filter className="w-3.5 h-3.5 mr-1" />
            Class:
          </span>
          {['ALL', '1A', '2A', '3A', 'SL', 'CC'].map((cls) => (
            <button
              key={cls}
              onClick={() => setSelectedClass(cls)}
              className={`px-2 py-0.5 rounded font-medium ${
                selectedClass === cls ? 'bg-railblue-700 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {cls}
            </button>
          ))}
        </div>
      </div>

      {/* Train Cards List */}
      <div className="space-y-4">
        {filteredTrains.length === 0 && !loading && (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
            No trains found matching the specified route and filters.
          </div>
        )}

        {filteredTrains.map((train) => (
          <div
            key={train.train_number}
            className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 hover:border-railblue-300 transition-all"
          >
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              {/* Train Header & Timings */}
              <div className="space-y-2 flex-1">
                <div className="flex items-center space-x-2.5">
                  <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-railnavy-900 text-white">
                    {train.train_number}
                  </span>
                  <h3 className="text-base font-bold text-slate-900">{train.train_name}</h3>
                  <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {train.running_status}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Source: {train.data_source}
                  </span>
                </div>

                <div className="flex items-center space-x-6 text-sm text-slate-600">
                  <div>
                    <span className="text-xs text-slate-400 block">Departure</span>
                    <span className="font-bold text-slate-900 text-base">{train.departure_time}</span>
                    <span className="text-xs text-slate-500 ml-1">({train.source})</span>
                  </div>

                  <div className="text-center px-4">
                    <span className="text-[11px] text-slate-400 block">{train.duration_formatted}</span>
                    <div className="w-20 h-0.5 bg-slate-300 my-1 relative">
                      <div className="absolute right-0 -top-1 w-2 h-2 border-t-2 border-r-2 border-slate-400 rotate-45"></div>
                    </div>
                    <span className="text-[10px] text-slate-500">{train.running_days}</span>
                  </div>

                  <div>
                    <span className="text-xs text-slate-400 block">Arrival</span>
                    <span className="font-bold text-slate-900 text-base">{train.arrival_time}</span>
                    <span className="text-xs text-slate-500 ml-1">({train.destination})</span>
                  </div>
                </div>
              </div>

              {/* Class Quotas & Seat Availabilities */}
              <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                {train.availabilities?.map((av) => (
                  <div
                    key={av.class_type}
                    className="p-2.5 min-w-[90px] rounded-lg border border-slate-200 bg-slate-50/70 text-center"
                  >
                    <div className="flex items-center justify-between text-xs font-bold text-slate-700 mb-0.5">
                      <span>{av.class_type}</span>
                      <span className="text-slate-500 font-normal">₹{av.fare}</span>
                    </div>
                    <div className={`text-xs font-bold ${
                      av.status === 'AVAILABLE'
                        ? 'text-emerald-700'
                        : av.status === 'RAC'
                        ? 'text-amber-700'
                        : 'text-rose-700'
                    }`}>
                      {av.status === 'AVAILABLE' ? `AVL ${av.seats_available}` : av.status}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
