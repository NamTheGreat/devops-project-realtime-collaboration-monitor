/**
 * BranchMap.jsx — Visual branch activity map for the Git Collaboration Monitor.
 *
 * Renders active branches as nodes with contributor avatars and last push
 * times. Branches that share recently modified files are connected with
 * dashed red lines indicating conflict risk. Pure CSS/SVG implementation.
 */
import React, { useMemo } from 'react';

function relativeShort(iso) {
    try {
        const diff = (Date.now() - new Date(iso).getTime()) / 1000;
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        return `${Math.floor(diff / 3600)}h ago`;
    } catch {
        return '—';
    }
}

export default function BranchMap({ events }) {
    const branchData = useMemo(() => {
        const map = {};
        const tenMinAgo = Date.now() - 600000;

        events.forEach((e) => {
            if (!e.branch) return;
            if (!map[e.branch]) {
                map[e.branch] = {
                    name: e.branch,
                    lastPush: e.timestamp,
                    actor: e.actor,
                    avatar: e.actor_avatar,
                    files: new Set(),
                };
            }
            if (e.timestamp > map[e.branch].lastPush) {
                map[e.branch].lastPush = e.timestamp;
                map[e.branch].actor = e.actor;
                map[e.branch].avatar = e.actor_avatar;
            }
            (e.files_changed || []).forEach((f) => {
                try {
                    if (new Date(e.timestamp).getTime() >= tenMinAgo) map[e.branch].files.add(f);
                } catch { /* ignore */ }
            });
        });

        return Object.values(map);
    }, [events]);

    // Find conflict connections
    const connections = useMemo(() => {
        const pairs = [];
        for (let i = 0; i < branchData.length; i++) {
            for (let j = i + 1; j < branchData.length; j++) {
                const a = branchData[i];
                const b = branchData[j];
                const overlap = [...a.files].filter((f) => b.files.has(f));
                if (overlap.length > 0) {
                    pairs.push({ from: i, to: j, files: overlap });
                }
            }
        }
        return pairs;
    }, [branchData]);

    if (branchData.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-text-muted text-xs">
                No branch activity yet
            </div>
        );
    }

    // Layout: arrange nodes in a row
    const nodeW = 120;
    const gap = 30;
    const totalW = branchData.length * nodeW + (branchData.length - 1) * gap;
    const svgW = Math.max(totalW + 40, 300);
    const svgH = 140;

    const getX = (idx) => 20 + idx * (nodeW + gap) + nodeW / 2;
    const nodeY = 70;

    return (
        <div className="overflow-x-auto">
            <svg width={svgW} height={svgH} className="mx-auto">
                {/* Conflict connections */}
                {connections.map((c, idx) => (
                    <line
                        key={idx}
                        x1={getX(c.from)}
                        y1={nodeY}
                        x2={getX(c.to)}
                        y2={nodeY}
                        stroke="#ff3b3b"
                        strokeWidth="1.5"
                        strokeDasharray="6 4"
                        opacity="0.6"
                    />
                ))}

                {/* Branch nodes */}
                {branchData.map((b, idx) => {
                    const cx = getX(idx);
                    const hasConflict = connections.some((c) => c.from === idx || c.to === idx);
                    return (
                        <g key={b.name}>
                            {/* Node circle */}
                            <circle
                                cx={cx}
                                cy={nodeY}
                                r={20}
                                fill={hasConflict ? '#1a0808' : '#141420'}
                                stroke={hasConflict ? '#ff3b3b' : '#4a9eff'}
                                strokeWidth="1.5"
                            />
                            {/* Avatar or initial inside */}
                            <text
                                x={cx}
                                y={nodeY + 4}
                                textAnchor="middle"
                                fill={hasConflict ? '#ff3b3b' : '#4a9eff'}
                                fontSize="12"
                                fontFamily="JetBrains Mono"
                            >
                                {(b.actor || '?')[0].toUpperCase()}
                            </text>
                            {/* Branch name below */}
                            <text
                                x={cx}
                                y={nodeY + 40}
                                textAnchor="middle"
                                fill="#888899"
                                fontSize="9"
                                fontFamily="JetBrains Mono"
                            >
                                {b.name.length > 16 ? b.name.slice(0, 14) + '…' : b.name}
                            </text>
                            {/* Last push time */}
                            <text
                                x={cx}
                                y={nodeY + 52}
                                textAnchor="middle"
                                fill="#555566"
                                fontSize="8"
                                fontFamily="JetBrains Mono"
                            >
                                {relativeShort(b.lastPush)}
                            </text>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
}
