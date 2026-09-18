import React, { useState } from 'react';
import { User, Mail, Phone, MapPin, Calendar, Train as TrainIcon, X, CheckCircle2, ArrowRight } from 'lucide-react';
import { registerPassenger, createJourney } from '../services/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onJourneyCreated: (journeyId: string) => void;
}

export const PassengerRegistrationModal: React.FC<Props> = ({ isOpen, onClose, onJourneyCreated }) => {
  const [step, setStep] = useState<1 | 2>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Passenger Info
  const [name, setName] = useState('Kishore Stalin');
  const [email, setEmail] = useState('kishore@example.com');
  const [phone, setPhone] = useState('+91 98401 23456');
  const [smsEnabled, setSmsEnabled] = useState(true);
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [passengerId, setPassengerId] = useState<string | null>(null);

  // Step 2: Journey Details
  const [fromStation, setFromStation] = useState('CBE');
  const [toStation, setToStation] = useState('NDLS');
  const [journeyDate, setJourneyDate] = useState('2026-09-20');
  const [trainNumber, setTrainNumber] = useState('12601');

  if (!isOpen) return null;

  const handleStep1Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!name.trim()) {
      setError('Full Name is required.');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please provide a valid email address.');
      return;
    }
    if (!phone.trim() || phone.length < 8) {
      setError('Please provide a valid mobile number with country code (e.g. +91 98401 23456).');
      return;
    }

    setLoading(true);
    try {
      const res = await registerPassenger({
        name,
        email,
        phone,
        email_notifications_enabled: emailEnabled,
        sms_notifications_enabled: smsEnabled
      });
      setPassengerId(res.passenger_id);
      setStep(2);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please check backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleStep2Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!fromStation || !toStation || !trainNumber) {
      setError('Please fill in all journey fields.');
      return;
    }

    setLoading(true);
    try {
      const journey = await createJourney({
        passenger_id: passengerId || undefined,
        from_station: fromStation,
        to_station: toStation,
        journey_date: journeyDate,
        train_number: trainNumber
      });
      onJourneyCreated(journey.journey_id);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create journey.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/60">
          <div>
            <div className="text-xs font-semibold tracking-wider text-cyan-400 uppercase">
              {step === 1 ? 'Step 1 of 2: Passenger Profile' : 'Step 2 of 2: Active Journey Setup'}
            </div>
            <h2 className="text-xl font-bold text-white mt-0.5">
              {step === 1 ? 'Start Your RailMind Journey' : 'Configure Monitored Corridor'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-3 text-sm text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl">
            {error}
          </div>
        )}

        {/* Step 1 Form */}
        {step === 1 ? (
          <form onSubmit={handleStep1Submit} className="p-6 space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Full Name</label>
              <div className="relative">
                <User className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Kishore Stalin"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="kishore@example.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Mobile Number (International Format)</label>
              <div className="relative">
                <Phone className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 98401 23456"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  required
                />
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800 space-y-2">
              <div className="text-xs font-semibold text-slate-300">Notification Alerts:</div>
              <label className="flex items-center gap-2.5 text-xs text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={smsEnabled}
                  onChange={(e) => setSmsEnabled(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-0"
                />
                <span>Receive SMS alerts when delay exceeds 30 minutes</span>
              </label>
              <label className="flex items-center gap-2.5 text-xs text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={emailEnabled}
                  onChange={(e) => setEmailEnabled(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-0"
                />
                <span>Receive structured Email comparison when alternatives are generated</span>
              </label>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm rounded-xl transition-all shadow-lg shadow-cyan-600/20 disabled:opacity-50"
              >
                {loading ? 'Registering...' : 'Continue'}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        ) : (
          /* Step 2 Form */
          <form onSubmit={handleStep2Submit} className="p-6 space-y-4">
            <div className="p-3 bg-cyan-950/30 border border-cyan-800/40 rounded-xl text-xs text-cyan-200">
              Passenger <span className="font-semibold text-white">{name}</span> registered. Enter your journey details to commence real-time RailRadar monitoring.
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">From Station Code</label>
                <div className="relative">
                  <MapPin className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    value={fromStation}
                    onChange={(e) => setFromStation(e.target.value.toUpperCase())}
                    placeholder="CBE"
                    className="w-full pl-10 pr-3 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white text-sm uppercase focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">To Station Code</label>
                <div className="relative">
                  <MapPin className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    value={toStation}
                    onChange={(e) => setToStation(e.target.value.toUpperCase())}
                    placeholder="NDLS"
                    className="w-full pl-10 pr-3 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white text-sm uppercase focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Journey Date</label>
                <div className="relative">
                  <Calendar className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                  <input
                    type="date"
                    value={journeyDate}
                    onChange={(e) => setJourneyDate(e.target.value)}
                    className="w-full pl-10 pr-3 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Train Number</label>
                <div className="relative">
                  <TrainIcon className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    value={trainNumber}
                    onChange={(e) => setTrainNumber(e.target.value)}
                    placeholder="12601"
                    className="w-full pl-10 pr-3 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="pt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-xs text-slate-400 hover:text-white transition-colors"
              >
                Back to profile
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm rounded-xl transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4" />
                {loading ? 'Creating Journey...' : 'Activate Monitoring'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
