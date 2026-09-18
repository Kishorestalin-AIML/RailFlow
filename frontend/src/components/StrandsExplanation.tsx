import React, { useState } from 'react';
import { Bot, Sparkles, Send, RefreshCw, Info, HelpCircle } from 'lucide-react';
import { RecommendationResult, DecisionResult, ImpactResult } from '../types';
import { fetchStrandsExplanation } from '../services/api';

interface StrandsExplanationProps {
  journeyId: string;
  recommendation?: RecommendationResult;
  decision?: DecisionResult;
  impact?: ImpactResult;
  initialExplanation?: string;
}

export const StrandsExplanation: React.FC<StrandsExplanationProps> = ({
  journeyId,
  recommendation,
  decision,
  impact,
  initialExplanation
}) => {
  const [explanation, setExplanation] = useState<string>(
    initialExplanation ||
    "Your train is currently running behind schedule. RailMind's deterministic engine has calculated the transfer buffer impact. Please review the structured summary below."
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [userQuery, setUserQuery] = useState<string>('');
  const [modelProvider, setModelProvider] = useState<string>('Strands Agents SDK (Local Execution)');

  const handleRefreshOrAsk = async (queryText?: string) => {
    setLoading(true);
    try {
      const res = await fetchStrandsExplanation(journeyId, queryText || undefined);
      setExplanation(res.explanation);
      if (res.model_provider) {
        setModelProvider(res.model_provider);
      }
    } catch (err) {
      console.error('Error contacting Strands Agent:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userQuery.trim()) return;
    handleRefreshOrAsk(userQuery);
    setUserQuery('');
  };

  return (
    <div className="bg-gradient-to-b from-white to-slate-50 rounded-xl border border-railblue-200 shadow-sm p-6 mb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-200/80 gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-railblue-900 text-cyan-300 shadow-xs">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-bold text-slate-900">Journey Assistant</h3>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-railblue-100 text-railblue-800 border border-railblue-300">
                Powered by AWS Strands
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Deterministic Decision Interpreter • {modelProvider}
            </p>
          </div>
        </div>

        <button
          onClick={() => handleRefreshOrAsk()}
          disabled={loading}
          className="self-start sm:self-auto px-3 py-1.5 rounded text-xs font-semibold text-railblue-800 bg-railblue-50 hover:bg-railblue-100 border border-railblue-200 transition-colors flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Regenerate Summary</span>
        </button>
      </div>

      {/* Main Natural Language Explanation Box */}
      <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-2xs mb-5">
        <div className="flex items-start space-x-3">
          <Sparkles className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
              Passenger Explanation
            </div>
            {loading ? (
              <div className="flex items-center space-x-2 text-xs text-slate-500 py-1">
                <div className="w-2 h-2 rounded-full bg-railblue-600 animate-bounce"></div>
                <div className="w-2 h-2 rounded-full bg-railblue-600 animate-bounce [animation-delay:0.2s]"></div>
                <div className="w-2 h-2 rounded-full bg-railblue-600 animate-bounce [animation-delay:0.4s]"></div>
                <span>Strands Agent synthesizing structured decision...</span>
              </div>
            ) : (
              <p className="text-sm text-slate-800 font-medium leading-relaxed">
                {explanation}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Structured 3-Part Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        {/* What Changed */}
        <div className="p-3.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
            1. What Changed?
          </span>
          <p className="text-xs text-slate-700 leading-relaxed font-medium">
            {recommendation?.what_happened ||
              (impact?.delay_minutes
                ? `Train ${impact.affected_train} incurred +${impact.delay_minutes} min delay.`
                : 'All trains operating on scheduled timetable.')}
          </p>
        </div>

        {/* Why Does It Matter */}
        <div className="p-3.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
            2. Why Does It Matter?
          </span>
          <p className="text-xs text-slate-700 leading-relaxed font-medium">
            {recommendation?.why_it_matters ||
              (decision?.reason ? decision.reason : 'No connection schedule breach detected.')}
          </p>
        </div>

        {/* What Options Exist */}
        <div className="p-3.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
            3. What Options Exist?
          </span>
          <p className="text-xs text-slate-700 leading-relaxed font-medium">
            {recommendation?.options && recommendation.options.length > 0
              ? recommendation.options.map(o => o.title).join(' • ')
              : 'Maintain normal travel itinerary and proceed to boarding.'}
          </p>
        </div>
      </div>

      {/* Interactive Passenger Inquiry */}
      <form onSubmit={handleFormSubmit} className="pt-3 border-t border-slate-200/80">
        <label className="block text-xs font-semibold text-slate-600 mb-1.5 flex items-center space-x-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-railblue-600" />
          <span>Ask Strands Assistant regarding this decision:</span>
        </label>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
            placeholder="e.g. Will I have enough time for platform transfer at Chennai?"
            className="flex-1 text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-railblue-500 focus:border-transparent bg-white"
          />
          <button
            type="submit"
            disabled={loading || !userQuery.trim()}
            className="px-3.5 py-2 rounded-lg text-xs font-semibold bg-railblue-700 hover:bg-railblue-800 text-white transition-colors flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
          >
            <span>Ask</span>
            <Send className="w-3 h-3" />
          </button>
        </div>
        <p className="text-[11px] text-slate-400 mt-1.5">
          Rule: Strands explains the deterministic decision and does not fabricate railway availability.
        </p>
      </form>
    </div>
  );
};
