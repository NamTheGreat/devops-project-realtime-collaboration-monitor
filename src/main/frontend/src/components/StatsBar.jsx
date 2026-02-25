/**
 * StatsBar.jsx — Top statistics bar for the Git Collaboration Monitor dashboard.
 *
 * Displays four key metrics: Events Today, Active Contributors,
 * Branches Modified, and Conflict Alerts. Numbers animate on change.
 * Also shows WebSocket connection status indicator.
 */
import React, { useEffect, useRef, useState } from 'react';

/** Animate a number from `from` to `to` over a short duration. */
function useAnimatedNumber(target) {
    const [display, setDisplay] = useState(target);
    const prev = useRef(target);

    useEffect(() => {
        const start = prev.current;
        const diff = target - start;
        if (diff === 0) return;

        const duration = 500;
        const startTime = performance.now();

        function tick(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            setDisplay(Math.round(start + diff * progress));
            if (progress < 1) requestAnimationFrame(tick);
        }

        requestAnimationFrame(tick);
        prev.current = target;
    }, [target]);

    return display;
}

function StatBlock({ label, value, color = 'text-text-primary' }) {
    const animated = useAnimatedNumber(value);
    return (
        <div className="stat-card min-w-[140px]">
            <span className={`text-2xl font-bold ${color}`}>{animated}</span>
            <span className="text-[10px] uppercase tracking-wider text-text-muted mt-1">{label}</span>
        </div>
    );
}

export default function StatsBar({ stats, connected }) {
    return (
        <div className="flex items-center justify-between px-4 py-2 border-b border-bg-tertiary bg-bg-secondary h-[60px]">
            <div className="flex gap-3">
                <StatBlock label="Events Today" value={stats.total_events_today} color="text-accent-green" />
                <StatBlock label="Active Contributors" value={stats.active_contributors} color="text-accent-blue" />
                <StatBlock label="Branches Modified" value={stats.branches_modified} color="text-accent-amber" />
                <StatBlock label="Conflict Alerts" value={stats.conflict_alerts} color="text-accent-red" />
            </div>

            <div className="flex items-center gap-2 text-xs">
                <span
                    className={`w-2 h-2 rounded-full ${connected
                            ? 'bg-accent-green animate-pulse-live glow-green'
                            : 'bg-accent-red glow-red'
                        }`}
                />
                <span className={connected ? 'text-accent-green' : 'text-accent-red'}>
                    {connected ? 'CONNECTED' : 'RECONNECTING\u2026'}
                </span>
            </div>
        </div>
    );
}
