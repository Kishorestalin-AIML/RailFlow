import {
  JourneyDetail,
  ImpactResult,
  DecisionResult,
  RecommendationResult,
  TrainSearchResult,
  SystemHealth,
  RailwayEventItem,
  StrandsExplanationResponse
} from '../types';

const API_BASE = 'http://127.0.0.1:8000';

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchJourney(idOrPnr: string): Promise<JourneyDetail> {
  const res = await fetch(`${API_BASE}/journey/${encodeURIComponent(idOrPnr)}`);
  if (!res.ok) {
    if (res.status === 404) throw new Error(`Journey '${idOrPnr}' not found.`);
    throw new Error('Failed to fetch journey details');
  }
  return res.json();
}

export async function fetchTrainSearch(
  origin: string,
  destination: string,
  date?: string
): Promise<TrainSearchResult[]> {
  const params = new URLSearchParams({ origin, destination });
  if (date) params.append('date', date);

  const res = await fetch(`${API_BASE}/trains/search?${params.toString()}`);
  if (!res.ok) throw new Error('Train search query failed');
  return res.json();
}

export async function fetchImpact(journeyId: string): Promise<ImpactResult> {
  const res = await fetch(`${API_BASE}/impact/${encodeURIComponent(journeyId)}`);
  if (!res.ok) throw new Error('Failed to fetch journey impact');
  return res.json();
}

export async function fetchDecision(journeyId: string): Promise<DecisionResult> {
  const res = await fetch(`${API_BASE}/decision/${encodeURIComponent(journeyId)}`);
  if (!res.ok) throw new Error('Failed to fetch journey decision');
  return res.json();
}

export async function fetchRecommendation(journeyId: string): Promise<RecommendationResult> {
  const res = await fetch(`${API_BASE}/recommendations/${encodeURIComponent(journeyId)}`);
  if (!res.ok) throw new Error('Failed to fetch journey recommendation');
  return res.json();
}

export async function fetchStrandsExplanation(
  journeyId: string,
  passengerQuery?: string
): Promise<StrandsExplanationResponse> {
  const res = await fetch(`${API_BASE}/ai/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ journey_id: journeyId, passenger_query: passengerQuery })
  });
  if (!res.ok) throw new Error('Strands explanation call failed');
  return res.json();
}

export async function fetchEvents(limit: number = 20): Promise<RailwayEventItem[]> {
  const res = await fetch(`${API_BASE}/events?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export async function simulateDelay(trainId: string, delayMinutes: number): Promise<any> {
  const res = await fetch(`${API_BASE}/simulate/delay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ train_id: trainId, delay_minutes: delayMinutes })
  });
  if (!res.ok) throw new Error('Delay simulation failed');
  return res.json();
}

export async function simulateCancellation(trainId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/simulate/cancel?train_id=${encodeURIComponent(trainId)}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Cancellation simulation failed');
  return res.json();
}

export async function simulateReset(): Promise<any> {
  const res = await fetch(`${API_BASE}/simulate/reset`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Reset simulation failed');
  return res.json();
}

export async function injectCustomEvent(eventData: {
  event_type: string;
  train_id: string;
  delay_minutes?: number;
  source?: string;
  details?: Record<string, any>;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(eventData)
  });
  if (!res.ok) throw new Error('Event injection failed');
  return res.json();
}

export function createEventSource(onMessage: (event: any) => void): () => void {
  const es = new EventSource(`${API_BASE}/events/stream`);
  es.addEventListener('railway_event', (e) => {
    try {
      const parsed = JSON.parse(e.data);
      onMessage(parsed);
    } catch (err) {
      console.error('SSE JSON error', err);
    }
  });
  return () => es.close();
}
