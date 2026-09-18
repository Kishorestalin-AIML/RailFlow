import React, { useState, useEffect } from 'react';
import { Search, Train, Calendar, User, Ticket, AlertCircle, RefreshCw } from 'lucide-react';
import { JourneyDetail, ImpactResult, DecisionResult, RecommendationResult, TrainSearchResult } from '../types';
import { fetchJourney, fetchImpact, fetchDecision, fetchRecommendation, fetchTrainSearch } from '../services/api';
import { JourneyTimeline } from '../components/JourneyTimeline';
import { ImpactPanel } from '../components/ImpactPanel';
import { DecisionPanel } from '../components/DecisionPanel';
import { StrandsExplanation } from '../components/StrandsExplanation';
import { AlternativeTrainsPanel } from '../components/AlternativeTrainsPanel';
import { LiveEventStream, PipelineStep } from '../components/LiveEventStream';
import { AlternativesModal } from '../components/AlternativesModal';

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

  // Alternatives Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [alternatives, setAlternatives] = useState<TrainSearchResult[]>([]);
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

      const [impData, decData, recData] = await Promise.all([
        fetchImpact(jData.journey_id),
        fetchDecision(jData.journey_id),
        fetchRecommendation(jData.journey_id)
      ]);

      setImpact(impData);
      setDecision(decData);
      setRecommendation(recData);
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
        fetchRecommendation(currentJourney.journey_id)
      ]).then(([imp, dec, rec]) => {
        setImpact(imp);
        setDecision(dec);
        setRecommendation(rec);
      }).catch(console.error);
    }
  }, [currentJourney?.journey_id, currentJourney?.updated_at]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pnrInput.trim()) return;
    loadJourneyDetails(pnrInput.trim());
  };

  const handleReviewAlternatives = async () => {
    if (!currentJourney) return;
    try {
      const transferStation = currentJourney.legs[0]?.to_station?.code || 'MAS';
      const finalStation = currentJourney.destination_station?.code || 'NDLS';
      const trains = await fetchTrainSearch(transferStation, finalStation);
      setAlternatives(trains);
      setIsModalOpen(true);
    } catch (err) {
      console.error('Failed to load alternative trains', err);
      showToast('Unable to fetch alternative connection trains');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 bg-railnavy-900 text-white px-4 py-3 rounded-lg shadow-xl border border-railnavy-700 flex items-center space-x-2 animate-bounce">
          <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
          <span className="text-xs font-semibold">{toastMessage}</span>
        </div>
      )}

      {/* Hero / Journey Search Area */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-3">
          <div>
            <h1 className="text-xl font-black text-slate-900 tracking-tight">
              Track Passenger Journey
            </h1>
            <p className="text-xs text-slate-500">
              Enter PNR or Journey ID to track real-time running state, buffer safety margins, and impact.
            </p>
          </div>

          <button
            onClick={() => {
              setPnrInput('DEMO123456');
              loadJourneyDetails('DEMO123456');
            }}
            className="self-start md:self-auto px-3 py-1.5 rounded-lg text-xs font-semibold bg-railblue-50 text-railblue-800 hover:bg-railblue-100 border border-railblue-200 transition-colors flex items-center space-x-1.5 cursor-pointer"
          >
            <Ticket className="w-3.5 h-3.5 text-railblue-600" />
            <span>Load Demo Journey (Coimbatore → Chennai → Delhi)</span>
          </button>
        </div>

        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          <div className="sm:col-span-6">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
              PNR / Journey ID
            </label>
            <div className="relative">
              <input
                type="text"
                value={pnrInput}
                onChange={(e) => setPnrInput(e.target.value)}
                placeholder="e.g. DEMO123456"
                className="w-full text-sm font-mono font-bold px-3.5 py-2.5 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-railblue-500 bg-white"
              />
              <Search className="w-4 h-4 text-slate-400 absolute right-3 top-3" />
            </div>
          </div>

          <div className="sm:col-span-4">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
              Journey Date
            </label>
            <div className="relative">
              <input
                type="date"
                value={dateInput}
                onChange={(e) => setDateInput(e.target.value)}
                className="w-full text-sm px-3.5 py-2.5 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-railblue-500 bg-white"
              />
              <Calendar className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>

          <div className="sm:col-span-2 flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-railblue-700 hover:bg-railblue-800 text-white transition-colors flex items-center justify-center space-x-1.5 cursor-pointer disabled:opacity-50"
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
          <div className="mt-3 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
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

          {/* Alternative Trains Panel (When At Risk or Missed) */}
          <AlternativeTrainsPanel
            recommendation={recommendation || undefined}
            transferStation={currentJourney.legs[0]?.to_station?.name || 'Chennai Central'}
            expectedArrival={currentJourney.legs[0]?.actual_arrival || '09:45'}
            onOpenModal={handleReviewAlternatives}
          />

          {/* Decision Support Panel */}
          {decision && (
            <DecisionPanel
              decision={decision}
              recommendation={recommendation || undefined}
              onReviewAlternatives={handleReviewAlternatives}
              onContinueMonitoring={() => showToast('Journey monitoring active. Polling railway running events.')}
              onSetAlert={() => showToast('10-Minute proximity alert registered for this passenger.')}
            />
          )}

          {/* AI Explanation Panel (Strands) */}
          <StrandsExplanation
            journeyId={currentJourney.journey_id}
            recommendation={recommendation || undefined}
            decision={decision || undefined}
            impact={impact || undefined}
            initialExplanation={recommendation?.ai_explanation}
          />

          {/* Live Operational Event Stream */}
          <LiveEventStream steps={pipelineSteps} />
        </>
      )}

      {/* Alternatives Modal */}
      {currentJourney && (
        <AlternativesModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          alternatives={alternatives}
          transferStation={currentJourney.legs[0]?.to_station?.name || 'Chennai Central'}
          expectedArrival={currentJourney.legs[0]?.actual_arrival || '09:45'}
        />
      )}
    </div>
  );
};
