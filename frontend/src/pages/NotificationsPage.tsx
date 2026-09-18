import React, { useState, useEffect } from 'react';
import { Bell, Mail, MessageSquare, CheckCircle, AlertTriangle, Clock, RefreshCw, Send, ShieldCheck } from 'lucide-react';
import { fetchNotifications } from '../services/api';
import { NotificationRecordItem } from '../types';

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationRecordItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedNotif, setSelectedNotif] = useState<NotificationRecordItem | null>(null);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await fetchNotifications();
      setNotifications(data);
      if (data.length > 0 && !selectedNotif) {
        setSelectedNotif(data[0]);
      }
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
            <Bell className="w-4 h-4" />
            <span>Passenger Dispatch Audit</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Passenger Notifications & Alerts</h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Automated SMS and Email notifications dispatched upon delay detection exceeding 30 minutes or transition to connection risk.
          </p>
        </div>

        <button
          onClick={loadNotifications}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Rules & Policy Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white">Threshold Trigger</div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Alerts only fire when real-time delay is ≥ 30 mins, eliminating spam for minor 1–2 min variations.
            </div>
          </div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3">
          <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white">Deduplication Lock</div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              A 15-minute suppression window prevents repeated messages for ongoing or duplicate events.
            </div>
          </div>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-start gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <Send className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white">Multi-Channel Delivery</div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Urgent SMS alert sent immediately; detailed Email sent with full alternative comparison table.
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid: Feed + Detail View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Feed List */}
        <div className="lg:col-span-5 bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
            <span className="text-xs font-bold text-white uppercase tracking-wider">Dispatched Messages</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-300">
              {notifications.length} Total
            </span>
          </div>

          <div className="divide-y divide-slate-800/60 max-h-[560px] overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                No notifications logged yet. When a meaningful disruption (≥ 30 min) occurs, SMS and Email alerts will appear here.
              </div>
            ) : (
              notifications.map((notif) => {
                const isSelected = selectedNotif?.notification_id === notif.notification_id;
                const isSMS = notif.channel === 'SMS';

                return (
                  <div
                    key={notif.notification_id}
                    onClick={() => setSelectedNotif(notif)}
                    className={`p-4 cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-cyan-950/30 border-l-2 border-cyan-400'
                        : 'hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {isSMS ? (
                          <div className="p-1.5 rounded-md bg-emerald-500/10 text-emerald-400">
                            <MessageSquare className="w-3.5 h-3.5" />
                          </div>
                        ) : (
                          <div className="p-1.5 rounded-md bg-cyan-500/10 text-cyan-400">
                            <Mail className="w-3.5 h-3.5" />
                          </div>
                        )}
                        <span className="text-xs font-semibold text-white">
                          {notif.channel} • {notif.notification_type}
                        </span>
                      </div>

                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                          notif.status === 'SENT'
                            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                            : notif.status === 'SIMULATED'
                            ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                            : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        }`}
                      >
                        {notif.status}
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-400 line-clamp-2 mt-2">
                      {notif.message}
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 font-mono">
                      <span>{notif.created_at}</span>
                      <span>{notif.notification_id}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Message Preview */}
        <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl p-6">
          {selectedNotif ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2.5 rounded-xl ${
                      selectedNotif.channel === 'SMS'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                    }`}
                  >
                    {selectedNotif.channel === 'SMS' ? (
                      <MessageSquare className="w-5 h-5" />
                    ) : (
                      <Mail className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      {selectedNotif.subject || `${selectedNotif.channel} Alert`}
                    </h3>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Type: <span className="text-cyan-300 font-medium">{selectedNotif.notification_type}</span>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    className={`text-xs font-semibold px-2.5 py-1 rounded-lg border ${
                      selectedNotif.status === 'SENT'
                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                        : 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                    }`}
                  >
                    Status: {selectedNotif.status}
                  </span>
                  <div className="text-[10px] text-slate-500 font-mono mt-1">
                    Sent: {selectedNotif.sent_at || selectedNotif.created_at}
                  </div>
                </div>
              </div>

              {/* Message Payload Content */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-2">Message Body</label>
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-200 font-mono whitespace-pre-line leading-relaxed">
                  {selectedNotif.message}
                </div>
              </div>

              {/* Provider Response Audit */}
              {selectedNotif.provider_response && (
                <div className="pt-2">
                  <label className="block text-[11px] font-semibold text-slate-500 mb-1">Gateway Diagnostics</label>
                  <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-[11px] text-slate-400 font-mono">
                    {selectedNotif.provider_response}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center text-center p-8 text-slate-500">
              <Mail className="w-10 h-10 opacity-30 mb-2" />
              <div className="text-sm font-medium">Select a notification from the list</div>
              <div className="text-xs text-slate-600 mt-1">Full delivery payloads and dispatch metadata will appear here</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
