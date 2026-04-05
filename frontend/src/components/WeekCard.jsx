/**
 * WeekCard.jsx — weekly learning plan card with colored left border
 */

const WEEK_COLORS = [
  { border: 'border-l-navy-500',   bg: 'bg-navy-50',   num: 'text-navy-600',   title: 'bg-navy-500' },
  { border: 'border-l-accent-400', bg: 'bg-accent-50', num: 'text-accent-600', title: 'bg-accent-500' },
  { border: 'border-l-emerald-400',bg: 'bg-emerald-50',num: 'text-emerald-600',title: 'bg-emerald-500' },
  { border: 'border-l-violet-400', bg: 'bg-violet-50', num: 'text-violet-600', title: 'bg-violet-500' },
];

export default function WeekCard({ plan }) {
  const { week, focus, goal, daily_time_minutes } = plan;
  const color = WEEK_COLORS[(week - 1) % 4];

  return (
    <div className={`card border-l-4 ${color.border} p-5 flex flex-col gap-3 h-full`}>
      {/* Week badge */}
      <div className="flex items-center gap-2">
        <span className={`w-7 h-7 rounded-lg ${color.title} text-white
                          text-xs font-bold flex items-center justify-center flex-shrink-0`}>
          {week}
        </span>
        <span className={`text-xs font-bold uppercase tracking-wider ${color.num}`}>
          Week {week}
        </span>
      </div>

      {/* Focus */}
      <div>
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-0.5">Focus</p>
        <p className="font-display font-bold text-navy-700 text-sm leading-snug capitalize">{focus}</p>
      </div>

      {/* Goal */}
      <div className={`${color.bg} rounded-xl p-3 flex-1`}>
        <p className="text-xs font-semibold text-slate-500 mb-1">🎯 Goal</p>
        <p className="text-sm text-slate-700 leading-relaxed">{goal}</p>
      </div>

      {/* Daily time */}
      <div className="flex items-center gap-1.5">
        <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-xs text-slate-500 font-medium">
          {daily_time_minutes} min/day
        </span>
      </div>
    </div>
  );
}