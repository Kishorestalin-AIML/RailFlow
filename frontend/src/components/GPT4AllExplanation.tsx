import React, { useState } from 'react';
import { Cpu, Sparkles, Send, HelpCircle, CheckCircle2, ShieldAlert, GitCompare } from 'lucide-react';
import { fetchGPT4AllExplanation } from '../services/api';

interface Props {
  journeyId: string;
  initialExplanation?: string;
}

export const GPT4AllExplanation: React.FC<Props> = ({ journeyId, initialExplanation }) => {
  const [query, setQuery] = useState('');
  const [explanation, setExplanation] = useState<string>(
    initialExplanation ||
      `What changed?
Train 12601 is currently monitored via RailRadar API live updates.

Why does it matter?
If delay exceeds the 30-minute threshold, your connection to Train 12615 at Chennai Central will be at risk.

Alternative ways to reach your destination:
Feasible alternatives from Chennai Central and nearby junctions will populate automatically upon disruption.

Important trade-offs:
Deterministic calculations prioritize earliest destination arrival while comparing seat confirmation (CNF vs RAC).`
  );
  const [loading, setLoading] = useState(false);
  const [modelInfo, setModelInfo] = useState<string>('GPT4All (Local LLM)');

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    try {
      const res = await fetchGPT4AllExplanation(journeyId, query);
      setExplanation(res.explanation);
      setModelInfo(`${res.model_provider} • ${res.model_name}`);
      setQuery('');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Helper to parse the 4 standard sections
  const renderFormattedExplanation = (text: string) => {
    const sections = text.split(/(?=What changed\?|Why does it matter\?|Alternative ways to reach your destination:|Important trade-offs:)/i);

    if (sections.length < 2) {
      return <div className="text-slate-200 text-sm whitespace-pre-line leading-relaxed">{text}</div>;
    }

    return (
      <div className="space-y-4">
        {sections.map((sec, idx) => {
          const lines = sec.trim().split('\n');
          const heading = lines[0];
          const body = lines.slice(1).join('\n').trim();

          const isTradeOff = heading.toLowerCase().includes('trade-off');
          const isWhatChanged = heading.toLowerCase().includes('what changed');
          const isWhyMatters = heading.toLowerCase().includes('why does it matter');
          const isAlternatives = heading.toLowerCase().includes('alternative');

          return (
            <div
              key={idx}
              className={`p-3.5 rounded-xl border ${
                isTradeOff
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : isWhyMatters
                  ? 'bg-rose-950/20 border-rose-500/20'
                  : isAlternatives
                  ? 'bg-cyan-950/20 border-cyan-500/20'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                {isTradeOff && <GitCompare className="w-4 h-4 text-amber-400" />}
                {isWhyMatters && <ShieldAlert className="w-4 h-4 text-rose-400" />}
                {isAlternatives && <Sparkles className="w-4 h-4 text-cyan-400" />}
                {isWhatChanged && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">{heading}</h4>
              </div>
              <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed pl-6">
                {body}
              </p>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="p-5 border-b border-slate-800 bg-gradient-to-r from-slate-950/80 via-slate-900 to-slate-950/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">RailMind Assistant</h3>
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                Powered by GPT4All
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Local LLM explanation engine strictly grounded in backend deterministic railway intelligence.
            </p>
          </div>
        </div>

        <div className="hidden sm:block text-right">
          <span className="text-[11px] font-mono text-purple-300/80 bg-purple-950/40 px-2.5 py-1 rounded-lg border border-purple-800/40">
            {modelInfo}
          </span>
        </div>
      </div>

      {/* Main Explanation Body */}
      <div className="p-5 space-y-4">
        {loading ? (
          <div className="p-6 text-center animate-pulse">
            <Sparkles className="w-6 h-6 text-purple-400 mx-auto mb-2 animate-spin" />
            <div className="text-xs text-slate-400 font-medium">GPT4All is synthesizing trade-offs from verified railway data...</div>
          </div>
        ) : (
          renderFormattedExplanation(explanation)
        )}

        {/* Quick Prompts */}
        <div className="pt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span className="text-[11px] font-semibold text-slate-500">Suggested Questions:</span>
          {[
            'Which option arrives earliest?',
            'Explain the RAC vs CNF trade-off',
            'Do any alternatives require a station transfer?'
          ].map((prompt, i) => (
            <button
              key={i}
              onClick={() => setQuery(prompt)}
              className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors border border-slate-700/60"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Passenger Interactive Query Input */}
        <form onSubmit={handleAsk} className="pt-2 flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask GPT4All about connection risks, station transfers, or RAC trade-offs..."
              className="w-full px-4 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 transition-all disabled:opacity-40 shadow-lg shadow-purple-600/20"
          >
            <span>Ask</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* System Prompt Strictness Badge */}
        <div className="pt-2 flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-800/60">
          <span className="flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
            <span>Zero-hallucination guarantee: GPT4All cannot invent train numbers, timings, or override backend feasibility.</span>
          </span>
          <span className="text-slate-500 font-mono">Offline Local Inference</span>
        </div>
      </div>
    </div>
  );
};
