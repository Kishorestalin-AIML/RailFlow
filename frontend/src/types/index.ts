export interface StationInfo {
  code: string;
  name: string;
  city: string;
  state: string;
  platforms: number;
}

export interface JourneyLegState {
  leg_order: number;
  train_number: string;
  train_name: string;
  from_station: StationInfo;
  to_station: StationInfo;
  scheduled_departure: string;
  scheduled_arrival: string;
  actual_departure?: string;
  actual_arrival?: string;
  delay_arrival_min: number;
  status: 'ON_TIME' | 'DELAYED' | 'CANCELLED' | 'RUNNING' | 'ARRIVED';
}

export interface JourneyDetail {
  journey_id: string;
  pnr: string;
  passenger_name: string;
  passenger_email?: string;
  source_station: StationInfo;
  destination_station: StationInfo;
  journey_date: string;
  journey_status: 'SAFE' | 'CONNECTION_AT_RISK' | 'MISSED' | 'CANCELLED' | 'DISRUPTED';
  legs: JourneyLegState[];
  connection_buffer_minutes?: number;
  minimum_safe_buffer_minutes: number;
  booking_status: string;
  booking_class: string;
  coach: string;
  berth_number: number;
  updated_at: string;
  data_source: string;
}

export interface ImpactResult {
  impact_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  affected_train: string;
  delay_minutes: number;
  remaining_buffer_minutes?: number;
  required_buffer_minutes: number;
  connection_train?: string;
  connection_departure?: string;
  expected_arrival?: string;
  status_summary: string;
}

export interface FeasibleAction {
  action_type: string;
  feasibility: 'FEASIBLE' | 'NOT_FEASIBLE' | 'REQUIRES_USER_ACTION' | 'INFORMATION_ONLY';
  title: string;
  description: string;
}

export interface DecisionResult {
  decision_id: string;
  journey_id: string;
  situation_status: 'SAFE' | 'AT_RISK' | 'MISSED' | 'CANCELLED';
  system_assessment: string;
  reason: string;
  feasible_actions: FeasibleAction[];
  timestamp: string;
}

export interface RecommendationAction {
  type: string;
  label: string;
  variant: 'primary' | 'secondary' | 'danger';
  payload?: any;
}

export interface RecommendationResult {
  id: string;
  journey_id: string;
  title: string;
  status: 'SAFE' | 'ACTION_REQUIRED' | 'CRITICAL_ALERT';
  what_happened: string;
  why_it_matters: string;
  options: Array<{
    option_id?: string;
    title: string;
    description: string;
    tag?: string;
  }>;
  actions: RecommendationAction[];
  ai_explanation?: string;
  created_at: string;
}

export interface TrainAvailabilityItem {
  class_type: string;
  status: string;
  seats_available: number;
  fare: number;
}

export interface TrainSearchResult {
  train_number: string;
  train_name: string;
  source: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  duration_formatted: string;
  running_days: string;
  running_status: string;
  delay_minutes: number;
  data_source: string;
  availabilities: TrainAvailabilityItem[];
}

export interface SystemHealth {
  status: string;
  database: string;
  data_adapter_mode: string;
  data_adapter_base_url?: string;
  strands_status: string;
  active_journeys_count: number;
  events_count: number;
  last_updated: string;
}

export interface RailwayEventItem {
  event_id: string;
  event_type: string;
  train_id: string;
  timestamp: string;
  source: string;
  payload: Record<string, any>;
}

export interface StrandsExplanationResponse {
  journey_id: string;
  structured_decision_summary: Record<string, any>;
  explanation: string;
  model_provider: string;
  model_name: string;
  timestamp: string;
}

export interface PassengerContactInfo {
  passenger_id?: string;
  name: string;
  email: string;
  phone: string;
  email_notifications_enabled: boolean;
  sms_notifications_enabled: boolean;
}

export interface AlternativeOptionItem {
  option_letter?: string;
  option_type: 'SAME_STATION' | 'ALTERNATIVE_STATION';
  train_number: string;
  train_name: string;
  station_code: string;
  station_name: string;
  departure_time: string;
  expected_destination_arrival: string;
  waiting_time_minutes: number;
  transfer_time_minutes: number;
  train_travel_minutes: number;
  total_journey_duration_minutes: number;
  availability: string;
  availability_status: string;
  fare?: number;
  formatted_fare: string;
  is_feasible: boolean;
  feasibility_reason: string;
}

export interface AlternativeComparisonMatrix {
  journey_id: string;
  current_journey: {
    train: string;
    train_name: string;
    station: string;
    station_code: string;
    departure: string;
    expected_destination_arrival: string;
    transfer_minutes: number;
    availability: string;
    fare: number;
    formatted_fare: string;
    status: string;
  };
  alternatives: AlternativeOptionItem[];
  all_evaluated_count: number;
  feasible_count: number;
}

export interface NotificationRecordItem {
  notification_id: string;
  passenger_id?: string;
  journey_id?: string;
  channel: 'SMS' | 'EMAIL';
  notification_type: string;
  subject?: string;
  message: string;
  status: 'SENT' | 'FAILED' | 'SIMULATED';
  provider_response?: string;
  created_at: string;
  sent_at?: string;
}

export interface GPT4AllExplanationResponse {
  journey_id: string;
  structured_decision_summary: Record<string, any>;
  explanation: string;
  model_provider: string;
  model_name: string;
  timestamp: string;
}
