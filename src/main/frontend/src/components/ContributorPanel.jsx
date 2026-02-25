/**
 * ContributorPanel.jsx — Contributor activity panel for the dashboard.
 *
 * Shows a ranked list of contributors active in the last hour with event
 * counts, CSS-only activity sparklines, and a branch activity section
 * that allows filtering the LiveFeed by branch.
 */
import React from 'react';

function Sparkline({ count, max }) {
    const pct = max > 0 ? (count / max) * 100 : 0;
    return (
        <div className="w-16 h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
            <div
                className="h-full bg-accent-green rounded-full transition-all duration-300"
                style={{ width: `${pct}%` }}
            />
        </div>
    );
}

function relativeShort(iso) {
    try {
        const diff = (Date.now() - new Date(iso).getTime()) / 1000;
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m`;
        return `${Math.floor(diff / 3600)}h`;
    } catch {
        return '—';
    }
}

export default function ContributorPanel({ events, onBranchFilter, activeBranch }) {
    // Compute contributor stats from events
    const oneHourAgo = Date.now() - 3600 * 1000;
    const recentEvents = events.filter((e) => {
        try { return new Date(e.timestamp).getTime() >= oneHourAgo; } catch { return false; }
    });

    const contribMap = {};
    recentEvents.forEach((e) => {
        if (!contribMap[e.actor]) {
            contribMap[e.actor] = { avatar: e.actor_avatar, count: 0, lastSeen: e.timestamp };
        }
        contribMap[e.actor].count += 1;
        if (e.timestamp > contribMap[e.actor].lastSeen) contribMap[e.actor].lastSeen = e.timestamp;
    });

    const contributors = Object.entries(contribMap)
        .map(([name, data]) => ({ name, ...data }))
        .sort((a, b) => b.count - a.count);

    const maxCount = contributors.length > 0 ? contributors[0].count : 1;

    // Gather branches
    const branchSet = new Set();
    events.forEach((e) => { if (e.branch) branchSet.add(e.branch); });
    const branches = Array.from(branchSet).sort();

    return (
        <div className="flex flex-col h-full border-l border-bg-tertiary">
            {/* Contributors */}
            <div className="panel-header">
                <span>CONTRIBUTORS</span>
                <span className="text-text-muted">{contributors.length}</span>
            </div>
            <div className="flex-1 overflow-y-auto">
                {contributors.length === 0 ? (
                    <div className="flex items-center justify-center h-24 text-text-muted text-xs">
                        No recent activity
                    </div>
                ) : (
                    contributors.map((c) => (
                        <div key={c.name} className="flex items-center gap-2 px-4 py-2 hover:bg-bg-secondary transition-colors">
                            {c.avatar ? (
                                <img src={c.avatar} alt={c.name} className="w-6 h-6 rounded-full" />
                            ) : (
                                <div className="w-6 h-6 rounded-full bg-bg-tertiary flex items-center justify-center text-[10px] text-text-muted">
                                    {c.name[0].toUpperCase()}
                                </div>
                            )}
                            <span className="text-xs text-text-primary flex-1 truncate">{c.name}</span>
                            <Sparkline count={c.count} max={maxCount} />
                            <span className="text-[10px] text-text-muted w-8 text-right">{c.count}</span>
                            <span className="text-[10px] text-text-muted w-10 text-right">{relativeShort(c.lastSeen)}</span>
                        </div>
                    ))
                )}
            </div>

            {/* Branch Activity */}
            <div className="panel-header">
                <span>BRANCH ACTIVITY</span>
                <span className="text-text-muted">{branches.length}</span>
            </div>
            <div className="p-3 flex flex-wrap gap-1.5 overflow-y-auto max-h-[140px]">
                {activeBranch && (
                    <button
                        onClick={() => onBranchFilter(null)}
                        className="branch-tag bg-accent-red/20 text-accent-red hover:bg-accent-red hover:text-bg-primary"
                    >
                        ✕ Clear
                    </button>
                )}
                {branches.map((b) => (
                    <button
                        key={b}
                        onClick={() => onBranchFilter(b)}
                        className={`branch-tag ${activeBranch === b ? 'bg-accent-blue text-bg-primary' : ''}`}
                    >
                        {b}
                    </button>
                ))}
                {branches.length === 0 && (
                    <span className="text-xs text-text-muted">No branches yet</span>
                )}
            </div>
        </div>
    );
}
