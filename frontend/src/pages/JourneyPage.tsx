import React, { useState, useEffect } from 'react';
import { Search, Train, Calendar, User, Ticket, AlertCircle, RefreshCw, GitCompare } from 'lucide-react';
import { JourneyDetail, ImpactResult, DecisionResult, RecommendationResult, TrainSearchResult, AlternativeComparisonMatrix } from '../types';
import { fetchJourney, fetchImpact, fetchDecision, fetchRecommendation, fetchAlternatives } from '../services/api';
import { JourneyTimeline } from '../components/JourneyTimeline';
import { ImpactPanel } from '../components/ImpactPanel';
import { DecisionPanel } from '../components/DecisionPanel';
import { GPT4AllExplanation } from '../components/GPT4AllExplanation';
import { AlternativeComparisonTable } from '../components/AlternativeComparisonTable';
import { LiveEventStream, PipelineStep } from '../components/LiveEventStream';

interface JourneyPageProps {
  currentJourney: JourneyDetail | null;
  onJourneyLoaded: (journey: JourneyDetail) => void;
  onNavigateToSearch: (origin?: string, dest?: string) => void;
  pipelineSteps: PipelineStep[];
}

export const JourneyPage: React.FC<JourneyPageProps> = ({
  currentJourney,
  onJourneyLoaded,
  onNavigateToSearch,
  pipelineSteps
}) => {
  const [pnrInput, setPnrInput] = useState('DEMO123456');
  const [dateInput, setDateInput] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [impact, setImpact] = useState<ImpactResult | null>(null);
  const [decision, setDecision] = useState<DecisionResult | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
  const [altMatrix, setAltMatrix] = useState<AlternativeComparisonMatrix | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const loadJourneyDetails = async (identifier: string) => {
    setLoading(true);
    setError(null);
    try {
      const jData = await fetchJourney(identifier);
      onJourneyLoaded(jData);

      const [impData, decData, recData, altsData] = await Promise.all([
        fetchImpact(jData.journey_id),
        fetchDecision(jData.journey_id),
        fetchRecommendation(jData.journey_id),
        fetchAlternatives(jData.journey_id).catch(() => null)
      ]);

      setImpact(impData);
      setDecision(decData);
      setRecommendation(recData);
      setAltMatrix(altsData);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load journey details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentJourney) {
      loadJourneyDetails('DEMO123456');
    } else {
      Promise.all([
        fetchImpact(currentJourney.journey_id),
        fetchDecision(currentJourney.journey_id),
        fetchRecommendation(currentJourney.journey_id),
        fetchAlternatives(currentJourney.journey_id).catch(() => null)
      ]).then(([imp, dec, rec, alts]) => {
        setImpact(imp);
        setDecision(dec);
        setRecommendation(rec);
        setAltMatrix(alts);
      }).catch(console.error);
    }
  }, [currentJourney?.journey_id, currentJourney?.updated_at]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pnrInput.trim()) return;
    loadJourneyDetails(pnrInput.trim());
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-2xl border border-slate-700 flex items-center space-x-2 animate-bounce">
          <span className="h-2 w-2 rounded-full bg-cyan-400"></span>
          <span className="text-xs font-semibold">{toastMessage}</span>
        </div>
      )}

      {/* Hero / Journey Search Area */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-4 border-b border-slate-800 gap-3">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">
              Real-Time Monitored Journey
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Live tracking powered by RailRadar API. Delays automatically trigger downstream impact analysis and alternative discovery.
            </p>
          </div>

          <button
            onClick={() => {
              setPnrInput('DEMO123456');
              loadJourneyDetails('DEMO123456');
            }}
            className="self-start md:self-auto px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-cyan-950/60 text-cyan-300 hover:bg-cyan-900/60 border border-cyan-800/60 transition-colors flex items-center space-x-1.5 cursor-pointer"
          >
            <Ticket className="w-3.5 h-3.5 text-cyan-400" />
            <span>Load Demo Journey (Coimbatore → Chennai → Delhi)</span>
          </button>
        </div>

        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          <div className="sm:col-span-6">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              PNR / Journey ID
            </label>
            <div className="relative">
              <input
                type="text"
                value={pnrInput}
                onChange={(e) => setPnrInput(e.target.value)}
                placeholder="e.g. DEMO123456"
                className="w-full text-sm font-mono font-bold px-3.5 py-2.5 rounded-xl border border-slate-700 bg-slate-950 text-white focus:outline-none focus:border-cyan-500"
              />
              <Search className="w-4 h-4 text-slate-500 absolute right-3 top-3" />
            </div>
          </div>

          <div className="sm:col-span-4">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Journey Date
            </label>
            <div className="relative">
              <input
                type="date"
                value={dateInput}
                onChange={(e) => setDateInput(e.target.value)}
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-700 bg-slate-950 text-white focus:outline-none focus:border-cyan-500"
              />
              <Calendar className="w-4 h-4 text-slate-500 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>

          <div className="sm:col-span-2 flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider bg-cyan-600 hover:bg-cyan-500 text-white transition-all flex items-center justify-center space-x-1.5 cursor-pointer disabled:opacity-50 shadow-lg shadow-cyan-600/20"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Track</span>
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Main Journey Content */}
      {currentJourney && (
        <>
          {/* Visual Timeline */}
          <JourneyTimeline journey={currentJourney} />

          {/* Live Impact Panel */}
          {impact && <ImpactPanel impact={impact} />}

          {/* Alternative Plans Table (Prominent upon risk) */}
          <AlternativeComparisonTable matrix={altMatrix} />

          {/* Decision Support Panel */}
          {decision && (
            <DecisionPanel
              decision={decision}
              recommendation={recommendation || undefined}
              onReviewAlternatives={() => showToast('Displaying alternative trains and stations above.')}
              onContinueMonitoring={() => showToast('Journey monitoring active. Polling railway running events.')}
              onSetAlert={() => showToast('10-Minute proximity alert registered for this passenger.')}
            />
          )}

          {/* AI Explanation Panel (GPT4All) */}
          <GPT4AllExplanation
            journeyId={currentJourney.journey_id}
            initialExplanation={recommendation?.ai_explanation}
          />

          {/* Live Operational Event Stream */}
          <LiveEventStream steps={pipelineSteps} />
        </>
      )}
    </div>
  );
};
