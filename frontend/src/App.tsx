import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { JourneyPage } from './pages/JourneyPage';
import { TrainSearchPage } from './pages/TrainSearchPage';
import { AlternativePlansPage } from './pages/AlternativePlansPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { PassengerRegistrationModal } from './components/PassengerRegistrationModal';
import { JourneyDetail, SystemHealth } from './types';
import { PipelineStep } from './components/LiveEventStream';
import { fetchHealth, fetchJourney, createEventSource } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'journey' | 'search' | 'alternatives' | 'notifications' | 'architecture'>('journey');
  const [currentJourney, setCurrentJourney] = useState<JourneyDetail | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [dataSource, setDataSource] = useState<string>('RailRadar API');
  const [isRegistrationOpen, setIsRegistrationOpen] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([
    {
      time: '14:10:00',
      step: 'BASELINE_ESTABLISHED',
      title: 'Real-Time Journey Monitor Active',
      detail: 'Train 12601 running status monitored via RailRadar API. Destination connection buffer is 50 minutes (SAFE).'
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

    // Subscribe to SSE updates from backend live updater
    const eventSource = createEventSource();
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        refreshSystemHealth();

        if (data && data.pipeline_steps && Array.isArray(data.pipeline_steps)) {
          setPipelineSteps((prev) => [...data.pipeline_steps, ...prev].slice(0, 20));
        }

        if (currentJourney) {
          reloadJourney(currentJourney.pnr);
        } else {
          reloadJourney('DEMO123456');
        }
      } catch (e) {
        // Heartbeat or ping
      }
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemHealth={systemHealth}
        dataSource={dataSource}
        onOpenRegistration={() => setIsRegistrationOpen(true)}
      />

      {/* Main Content Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
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

        {activeTab === 'alternatives' && (
          <AlternativePlansPage journeyId={currentJourney?.journey_id || 'JRN-DEMO-01'} />
        )}

        {activeTab === 'notifications' && <NotificationsPage />}

        {activeTab === 'architecture' && (
          <ArchitecturePage systemHealth={systemHealth} />
        )}
      </main>

      {/* Passenger Registration Modal */}
      <PassengerRegistrationModal
        isOpen={isRegistrationOpen}
        onClose={() => setIsRegistrationOpen(false)}
        onJourneyCreated={(journeyId) => {
          reloadJourney(journeyId);
          setActiveTab('journey');
        }}
      />

      {/* Operations Theme Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-6 text-slate-400 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-white">RailMind</span>
            <span>• Real-Time Railway Journey Intelligence</span>
            <span className="text-slate-500">| Powered by RailRadar API</span>
          </div>

          <div className="flex items-center space-x-4 text-slate-400 font-mono text-[11px]">
            <span>FastAPI + SQLite3</span>
            <span>•</span>
            <span>RailRadar Live API</span>
            <span>•</span>
            <span>GPT4All Local LLM</span>
            <span>•</span>
            <span>SMS + Email Alerts</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
