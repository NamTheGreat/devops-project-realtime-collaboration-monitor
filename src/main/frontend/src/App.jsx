/**
 * App.jsx — Root component for the Git Collaboration Monitor dashboard.
 *
 * Manages WebSocket connection with exponential backoff reconnection,
 * fetches recent events and stats, and orchestrates all child panels.
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import StatsBar from './components/StatsBar';
import AlertBanner from './components/AlertBanner';
import LiveFeed from './components/LiveFeed';
import ContributorPanel from './components/ContributorPanel';
import BranchMap from './components/BranchMap';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`;
const API_BASE = '';

export default function App() {
    const [events, setEvents] = useState([]);
    const [stats, setStats] = useState({
        total_events_today: 0,
        active_contributors: 0,
        branches_modified: 0,
        conflict_alerts: 0,
    });
    const [connected, setConnected] = useState(false);
    const [branchFilter, setBranchFilter] = useState(null);
    const wsRef = useRef(null);
    const reconnectDelay = useRef(3000);

    // --- WebSocket connection with exponential backoff ---
    const connectWs = useCallback(() => {
        try {
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                setConnected(true);
                reconnectDelay.current = 3000;
            };

            ws.onmessage = (msg) => {
                try {
                    const event = JSON.parse(msg.data);
                    setEvents((prev) => [event, ...prev].slice(0, 200));
                } catch {
                    // Ignore non-JSON messages
                }
            };

            ws.onclose = () => {
                setConnected(false);
                const delay = Math.min(reconnectDelay.current, 30000);
                reconnectDelay.current = delay * 1.5;
                setTimeout(connectWs, delay);
            };

            ws.onerror = () => {
                ws.close();
            };
        } catch {
            setTimeout(connectWs, reconnectDelay.current);
        }
    }, []);

    // --- Fetch recent events on mount ---
    useEffect(() => {
        async function fetchRecent() {
            try {
                const res = await fetch(`${API_BASE}/events/recent`);
                if (res.ok) {
                    const data = await res.json();
                    setEvents((prev) => {
                        const ids = new Set(prev.map((e) => e.id));
                        const merged = [...prev];
                        data.forEach((e) => { if (!ids.has(e.id)) merged.push(e); });
                        return merged.slice(0, 200);
                    });
                }
            } catch {
                // Backend not ready yet — silently ignore
            }
        }
        fetchRecent();
        connectWs();
        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, [connectWs]);

    // --- Poll stats every 30 seconds ---
    useEffect(() => {
        async function fetchStats() {
            try {
                const res = await fetch(`${API_BASE}/stats`);
                if (res.ok) setStats(await res.json());
            } catch {
                // Silently ignore
            }
        }
        fetchStats();
        const interval = setInterval(fetchStats, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col h-full bg-bg-primary">
            {/* Stats bar */}
            <StatsBar stats={stats} connected={connected} />

            {/* Alert banner */}
            <AlertBanner events={events} />

            {/* Main content */}
            <div className="flex flex-1 overflow-hidden">
                {/* Live Feed — 60% */}
                <div className="w-[60%] flex flex-col">
                    <LiveFeed events={events} branchFilter={branchFilter} />
                </div>

                {/* Right panel — 40% */}
                <div className="w-[40%] flex flex-col">
                    {/* Contributor panel and branch tags */}
                    <div className="flex-1 overflow-hidden">
                        <ContributorPanel
                            events={events}
                            onBranchFilter={setBranchFilter}
                            activeBranch={branchFilter}
                        />
                    </div>

                    {/* Branch map at bottom */}
                    <div className="border-t border-bg-tertiary">
                        <div className="panel-header">
                            <span>BRANCH MAP</span>
                        </div>
                        <div className="h-[160px] bg-bg-card">
                            <BranchMap events={events} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
