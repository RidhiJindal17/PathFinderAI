/**
 * BridgeSkillCard.jsx — bridge skill with XAI explanation, priority, YouTube link
 */

const PRIORITY_CONFIG = {
  high:   { border: 'border-l-red-400',    badge: 'bg-red-50 text-red-700 border-red-200',    label: '🔴 High Priority' },
  medium: { border: 'border-l-accent-400', badge: 'bg-accent-50 text-accent-700 border-accent-200', label: '🟠 Medium' },
  low:    { border: 'border-l-slate-300',  badge: 'bg-slate-100 text-slate-600 border-slate-200',   label: '⚪ Low' },
};

export default function BridgeSkillCard({ bridgeSkill, explanation }) {
  const { skill, priority, similarity_score } = bridgeSkill;
  const config = PRIORITY_CONFIG[priority] || PRIORITY_CONFIG.low;

  const why         = explanation?.why_needed     || '';
  const ytQuery     = explanation?.youtube_query  || `${skill} for beginners full course free 2024`;
  const weeks       = explanation?.estimated_weeks;
  const difficulty  = explanation?.difficulty;
  const ytUrl       = `https://www.youtube.com/results?search_query=${encodeURIComponent(ytQuery)}`;

  const gapPct = Math.round((1 - (similarity_score || 0)) * 100);

  return (
    <div className={`card border-l-4 ${config.border} p-5 transition-all duration-200 hover:shadow-card-hover`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="font-display font-bold text-navy-700 capitalize text-base">{skill}</h3>
          <span className={`chip border text-xs ${config.badge}`}>{config.label}</span>
        </div>
        {gapPct > 0 && (
          <span className="text-xs text-slate-400 font-mono flex-shrink-0 bg-slate-50 px-2 py-0.5 rounded-md">
            {gapPct}% gap
          </span>
        )}
      </div>

      {why && (
        <p className="text-sm text-slate-600 leading-relaxed mb-4 border-l-2 border-slate-200 pl-3 italic">
          "{why}"
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2 mt-auto">
        {/* YouTube button */}
        <a
          href={ytUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                     bg-red-50 text-red-700 border border-red-200
                     text-xs font-semibold hover:bg-red-100 transition-colors duration-150"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
          </svg>
          Free Course
        </a>

        {weeks && (
          <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg
                           bg-navy-50 text-navy-700 text-xs font-medium border border-navy-100">
            ⏱ {weeks} week{weeks > 1 ? 's' : ''}
          </span>
        )}

        {difficulty && (
          <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg
                           bg-slate-50 text-slate-600 text-xs font-medium border border-slate-100 capitalize">
            📊 {difficulty}
          </span>
        )}
      </div>
    </div>
  );
}