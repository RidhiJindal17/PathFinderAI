/**
 * MatchScore.jsx — animated circular progress score display
 */
export default function MatchScore({ score }) {
  const radius      = 54;
  const circumference = 2 * Math.PI * radius;
  const filled      = ((score || 0) / 100) * circumference;
  const gap         = circumference - filled;

  const color = score >= 85
    ? { stroke: '#10b981', text: 'text-emerald-400', label: 'Strong Fit', bg: 'bg-emerald-500/10' }
    : score >= 60
    ? { stroke: '#8b5cf6', text: 'text-accent-400',  label: 'Good Potential', bg: 'bg-accent-500/10' }
    : score >= 40
    ? { stroke: '#f59e0b', text: 'text-amber-400',  label: 'Partial Match', bg: 'bg-amber-500/10' }
    : { stroke: '#f43f5e', text: 'text-rose-400',    label: 'Major Gaps',    bg: 'bg-rose-500/10'    };

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-36 h-36">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
          {/* Track */}
          <circle
            cx="64" cy="64" r={radius}
            fill="none" stroke="#e2e8f0" strokeWidth="10"
          />
          {/* Progress */}
          <circle
            cx="64" cy="64" r={radius}
            fill="none"
            stroke={color.stroke}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${filled} ${gap}`}
            style={{ transition: 'stroke-dasharray 1.2s cubic-bezier(0.4,0,0.2,1)' }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`font-display font-bold text-3xl ${color.text}`}>
            {score}%
          </span>
          <span className="text-slate-400 text-xs font-medium">Match</span>
        </div>
      </div>
      {/* Label badge */}
      <span className={`chip ${color.bg} ${color.text} border-0 text-xs font-semibold px-3 py-1`}>
        {color.label}
      </span>
    </div>
  );
}