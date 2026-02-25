/**
 * AlertBanner.jsx — Conflict alert banner for the Git Collaboration Monitor.
 *
 * Only renders when active conflict alerts exist. Shows severity-coloured
 * banners with conflict details. Alerts auto-dismiss after 60 seconds
 * and can be manually dismissed.
 */
import React, { useEffect, useState } from 'react';

export default function AlertBanner({ events }) {
    const [dismissed, setDismissed] = useState(new Set());
    const [timers, setTimers] = useState({});

    // Gather alerts from events
    const alerts = events
        .filter((e) => e.alert && !dismissed.has(e.id))
        .map((e) => ({ ...e.alert, eventId: e.id }));

    // Auto-dismiss after 60 seconds
    useEffect(() => {
        alerts.forEach((alert) => {
            if (!timers[alert.eventId]) {
                const t = setTimeout(() => {
                    setDismissed((prev) => new Set(prev).add(alert.eventId));
                }, 60000);
                setTimers((prev) => ({ ...prev, [alert.eventId]: t }));
            }
        });
        return () => {
            // Cleanup not needed on unmount since alerts clear naturally
        };
    }, [alerts.length]);

    const dismiss = (eventId) => {
        setDismissed((prev) => new Set(prev).add(eventId));
        if (timers[eventId]) clearTimeout(timers[eventId]);
    };

    if (alerts.length === 0) return null;

    return (
        <div className="border-b border-bg-tertiary">
            {alerts.map((alert) => (
                <div
                    key={alert.eventId}
                    className={`alert-bar ${alert.severity === 'high'
                            ? 'bg-accent-red/10 border-accent-red/30 text-accent-red'
                            : 'bg-accent-amber/10 border-accent-amber/30 text-accent-amber'
                        }`}
                >
                    <span className="text-lg">⚠</span>
                    <span className="flex-1 font-mono text-xs">{alert.message}</span>
                    <span className="text-[10px] uppercase opacity-60">{alert.severity}</span>
                    <button
                        onClick={() => dismiss(alert.eventId)}
                        className="ml-2 opacity-50 hover:opacity-100 transition-opacity text-xs"
                        aria-label="Dismiss alert"
                    >
                        ✕
                    </button>
                </div>
            ))}
        </div>
    );
}
