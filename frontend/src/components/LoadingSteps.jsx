/**
 * LoadingSteps.jsx — animated pipeline progress indicator
 */

const STEPS = [
  { id: 1, label: 'Parsing resume',       icon: '📄', key: 'resume_parsed' },
  { id: 2, label: 'Analyzing skill gaps', icon: '🔍', key: 'gap_analyzed' },
  { id: 3, label: 'Generating roadmap',   icon: '🤖', key: 'roadmap_generated' },
  { id: 4, label: 'Fetching GitHub',      icon: '🐙', key: 'github_fetched' },
];

export default function LoadingSteps({ currentStep = 0, completedSteps = {} }) {
  return (
    <div className="w-full max-w-sm mx-auto py-6">
      {/* Bouncing dots */}
      <div className="flex items-center justify-center gap-1.5 mb-8">
        {[0, 1, 2].map(i => (
          <span
            key={i}
            className="w-2.5 h-2.5 rounded-full bg-accent-500 inline-block"
            style={{ animation: `bounceDot 1.2s infinite ${i * 200}ms` }}
          />
        ))}
      </div>

      <div className="space-y-3">
        {STEPS.map((step, idx) => {
          const done    = completedSteps[step.key] === true;
          const active  = idx === currentStep && !done;
          const pending = idx > currentStep && !done;

          return (
            <div
              key={step.id}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-500 ${
                done    ? 'bg-emerald-50 border border-emerald-200'
                : active  ? 'bg-navy-50 border border-navy-200 shadow-sm'
                : pending ? 'bg-white border border-slate-100 opacity-40'
                : 'bg-white border border-slate-100 opacity-40'
              }`}
            >
              {/* Icon / spinner / check */}
              <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                              bg-white shadow-sm border border-slate-100">
                {done ? (
                  <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : active ? (
                  <svg className="w-4 h-4 text-navy-600 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                ) : (
                  <span className="text-sm">{step.icon}</span>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className={`text-sm font-semibold truncate ${
                  done ? 'text-emerald-700' : active ? 'text-navy-700' : 'text-slate-400'
                }`}>
                  {step.label}
                </p>
                {active && (
                  <p className="text-xs text-navy-400 mt-0.5 animate-pulse">In progress…</p>
                )}
                {done && (
                  <p className="text-xs text-emerald-500 mt-0.5">Complete</p>
                )}
              </div>

              {done && (
                <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
          );
        })}
      </div>

      <p className="text-center text-xs text-slate-400 mt-6 font-medium">
        This takes 15–30 seconds · Please don't close this tab
      </p>
    </div>
  );
}