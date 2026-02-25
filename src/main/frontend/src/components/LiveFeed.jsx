/**
 * LiveFeed.jsx — Real-time event feed for the Git Collaboration Monitor.
 *
 * Renders a scrollable list of GitEvent objects with colour-coded dots,
 * avatars, human-readable titles, relative timestamps, and collapsible
 * file change lists for push events. New events animate in from the top.
 */
import React, { useState } from 'react';

const DOT_COLORS = {
    push: 'bg-accent-green',
    pull_request: 'bg-accent-blue',
    merge: 'bg-accent-blue',
    branch_create: 'bg-accent-amber',
    branch_delete: 'bg-accent-amber',
    issues: 'bg-text-secondary',
};

function relativeTime(iso) {
    try {
        const diff = (Date.now() - new Date(iso).getTime()) / 1000;
        if (diff < 60) return `${Math.floor(diff)}s ago`;
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    } catch {
        return '';
    }
}

function EventCard({ event }) {
    const [expanded, setExpanded] = useState(false);
    const dotColor = DOT_COLORS[event.event_type] || 'bg-text-muted';
    const hasFiles = event.files_changed && event.files_changed.length > 0;
    const hasAlert = !!event.alert;

    return (
        <div className={`event-card ${hasAlert ? 'border-l-2 border-l-accent-red' : ''}`}>
            {/* Colour dot */}
            <span className={`event-dot ${dotColor}`} />

            {/* Avatar */}
            {event.actor_avatar ? (
                <img
                    src={event.actor_avatar}
                    alt={event.actor}
                    className="w-8 h-8 rounded-full flex-shrink-0 mt-0.5"
                />
            ) : (
                <div className="w-8 h-8 rounded-full bg-bg-tertiary flex-shrink-0 flex items-center justify-center text-xs text-text-muted">
                    {(event.actor || '?')[0].toUpperCase()}
                </div>
            )}

            {/* Content */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-accent-green truncate">{event.actor}</span>
                    <span className="text-[10px] text-text-muted">{relativeTime(event.timestamp)}</span>
                </div>
                <p className="text-sm text-text-primary truncate">{event.title}</p>
                <span className="text-[10px] text-text-muted">{event.repository}</span>

                {/* Collapsible file list */}
                {hasFiles && (
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="block mt-1 text-[10px] text-accent-blue hover:underline"
                    >
                        {expanded ? '▾ Hide' : '▸ Show'} {event.files_changed.length} file(s)
                    </button>
                )}
                {expanded && hasFiles && (
                    <ul className="mt-1 space-y-0.5 text-[11px] text-text-secondary font-mono">
                        {event.files_changed.map((f, i) => (
                            <li key={i} className="truncate">
                                <span className="text-text-muted mr-1">•</span> {f}
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

export default function LiveFeed({ events, branchFilter }) {
    const filtered = branchFilter
        ? events.filter((e) => e.branch === branchFilter)
        : events;

    // Cap at 100 events in the DOM
    const visible = filtered.slice(0, 100);

    return (
        <div className="flex flex-col h-full">
            <div className="panel-header">
                <span>
                    LIVE FEED
                    {branchFilter && (
                        <span className="ml-2 text-accent-blue">— {branchFilter}</span>
                    )}
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent-red animate-pulse-live" />
                    <span className="text-accent-red text-[10px]">LIVE</span>
                </span>
            </div>
            <div className="flex-1 overflow-y-auto">
                {visible.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-text-muted text-sm">
                        Waiting for events…
                    </div>
                ) : (
                    visible.map((ev) => <EventCard key={ev.id} event={ev} />)
                )}
            </div>
        </div>
    );
}
