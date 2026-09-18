import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { JourneyPage } from './pages/JourneyPage';
import { TrainSearchPage } from './pages/TrainSearchPage';
import { SimulationConsole } from './pages/SimulationConsole';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { JourneyDetail, SystemHealth } from './types';
import { PipelineStep } from './components/LiveEventStream';
import { fetchHealth, fetchJourney, createEventSource } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'journey' | 'search' | 'simulation' | 'architecture'>('journey');
  const [currentJourney, setCurrentJourney] = useState<JourneyDetail | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [dataSource, setDataSource] = useState<string>('SIMULATED DATA');
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([
    {
      time: '14:10:00',
      step: 'BASELINE_ESTABLISHED',
      title: 'Journey Baseline Active',
      detail: 'Train 12601 on schedule (Arrival 08:30). Transfer buffer to Train 12615 is 50 minutes (SAFE).'
    }
  ]);

  const refreshSystemHealth = async () => {
    try {
      const h = await fetchHealth();
      setSystemHealth(h);
      setDataSource(h.data_adapter_mode);
    } catch (err) {
      console.error('Error fetching system health', err);
    }
  };

  const reloadJourney = async (pnrOrId: string = 'DEMO123456') => {
    try {
      const j = await fetchJourney(pnrOrId);
      setCurrentJourney(j);
      setDataSource(j.data_source);
    } catch (err) {
      console.error('Error reloading journey', err);
    }
  };

  useEffect(() => {
    refreshSystemHealth();
    reloadJourney('DEMO123456');

    // Subscribe to SSE updates from backend
    const unsubscribe = createEventSource((eventData) => {
      console.log('Real-time event from backend SSE:', eventData);
      refreshSystemHealth();

      if (eventData && eventData.pipeline_steps && Array.isArray(eventData.pipeline_steps)) {
        setPipelineSteps((prev) => [...eventData.pipeline_steps, ...prev].slice(0, 15));
      }

      if (currentJourney) {
        reloadJourney(currentJourney.pnr);
      } else {
        reloadJourney('DEMO123456');
      }
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="min-h-screen bg-[#F5F7FA] flex flex-col">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemHealth={systemHealth}
        dataSource={dataSource}
      />

      {/* Main Content Body */}
      <main className="flex-1">
        {activeTab === 'journey' && (
          <JourneyPage
            currentJourney={currentJourney}
            onJourneyLoaded={(j) => {
              setCurrentJourney(j);
              setDataSource(j.data_source);
            }}
            onNavigateToSearch={(origin, dest) => {
              setActiveTab('search');
            }}
            pipelineSteps={pipelineSteps}
          />
        )}

        {activeTab === 'search' && <TrainSearchPage />}

        {activeTab === 'simulation' && (
          <SimulationConsole
            onEventInjected={() => {
              if (currentJourney) {
                reloadJourney(currentJourney.pnr);
              } else {
                reloadJourney('DEMO123456');
              }
              refreshSystemHealth();
            }}
          />
        )}

        {activeTab === 'architecture' && (
          <ArchitecturePage systemHealth={systemHealth} />
        )}
      </main>

      {/* Operations Theme Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-slate-500 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-800">RailMind</span>
            <span>• Real-Time Railway Journey Intelligence</span>
            <span className="text-slate-400">| Track 1 Prototype</span>
          </div>

          <div className="flex items-center space-x-4 text-slate-600 font-mono text-[11px]">
            <span>FastAPI + SQLite3</span>
            <span>•</span>
            <span>AWS Strands Agents SDK v1.56</span>
            <span>•</span>
            <span>React + Vite</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
