import React, { useState, useEffect } from 'react';
import { GitCompare, RefreshCw, AlertCircle, Sparkles, MapPin } from 'lucide-react';
import { AlternativeComparisonTable } from '../components/AlternativeComparisonTable';
import { GPT4AllExplanation } from '../components/GPT4AllExplanation';
import { fetchAlternatives } from '../services/api';
import { AlternativeComparisonMatrix } from '../types';

interface Props {
  journeyId: string;
}

export const AlternativePlansPage: React.FC<Props> = ({ journeyId }) => {
  const [matrix, setMatrix] = useState<AlternativeComparisonMatrix | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAlternatives = async () => {
    setLoading(true);
    try {
      const data = await fetchAlternatives(journeyId);
      setMatrix(data);
    } catch (err) {
      console.error('Failed to load alternatives:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlternatives();
  }, [journeyId]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
            <GitCompare className="w-4 h-4" />
            <span>Multi-Route Decision Support</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Alternative Trains & Stations</h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Automatically evaluated backup corridors from the arrival junction and adjacent stations based on live RailRadar running state.
          </p>
        </div>

        <button
          onClick={loadAlternatives}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Recalculate Options</span>
        </button>
      </div>

      {/* Alternative Plans Table */}
      <AlternativeComparisonTable matrix={matrix} loading={loading} />

      {/* GPT4All Natural Language Trade-off Assistant */}
      <GPT4AllExplanation journeyId={journeyId} />
    </div>
  );
};
