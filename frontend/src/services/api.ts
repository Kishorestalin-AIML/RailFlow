import {
  JourneyDetail,
  ImpactResult,
  DecisionResult,
  RecommendationResult,
  TrainSearchResult,
  SystemHealth,
  RailwayEventItem,
  AlternativeComparisonMatrix,
  NotificationRecordItem,
  GPT4AllExplanationResponse,
  PassengerContactInfo
} from '../types';

const API_BASE = 'http://127.0.0.1:8000';

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchSystemStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/system/status`);
  if (!res.ok) throw new Error('System status query failed');
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

export async function registerPassenger(data: PassengerContactInfo): Promise<any> {
  const res = await fetch(`${API_BASE}/passengers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Passenger registration failed');
  return res.json();
}

export async function createJourney(data: {
  passenger_id?: string;
  from_station: string;
  to_station: string;
  journey_date: string;
  train_number: string;
}): Promise<JourneyDetail> {
  const res = await fetch(`${API_BASE}/journey`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Journey creation failed');
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

export async function fetchAlternatives(journeyId: string): Promise<AlternativeComparisonMatrix> {
  const res = await fetch(`${API_BASE}/alternatives/${encodeURIComponent(journeyId)}`);
  if (!res.ok) throw new Error('Failed to fetch journey alternatives');
  return res.json();
}

export async function fetchStationAlternatives(journeyId: string): Promise<any[]> {
  const res = await fetch(`${API_BASE}/alternatives/stations/${encodeURIComponent(journeyId)}`);
  if (!res.ok) throw new Error('Failed to fetch station alternatives');
  return res.json();
}

export async function fetchGPT4AllExplanation(
  journeyId: string,
  passengerQuery?: string
): Promise<GPT4AllExplanationResponse> {
  const res = await fetch(`${API_BASE}/ai/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ journey_id: journeyId, passenger_query: passengerQuery })
  });
  if (!res.ok) throw new Error('GPT4All explanation call failed');
  return res.json();
}

// Backward-compatibility alias
export const fetchStrandsExplanation = fetchGPT4AllExplanation;

export async function fetchNotifications(passengerId?: string): Promise<NotificationRecordItem[]> {
  const url = passengerId ? `${API_BASE}/notifications/${encodeURIComponent(passengerId)}` : `${API_BASE}/notifications`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch notifications log');
  return res.json();
}

export async function fetchEvents(limit: number = 20): Promise<RailwayEventItem[]> {
  const res = await fetch(`${API_BASE}/events?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export function createEventSource(): EventSource {
  return new EventSource(`${API_BASE}/events/stream`);
}
