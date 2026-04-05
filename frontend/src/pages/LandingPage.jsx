import { Link } from 'react-router-dom'

const FEATURES = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
    title: 'AI Mentor Guidance',
    desc:  'Candid feedback on why you are not being selected and exactly how to fix it.',
    bg: 'bg-accent-500/10', color: 'text-accent-400',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    title: 'Smart Roadmaps',
    desc:  'Bespoke 3-stage learning paths with direct links to the best free content on the web.',
    bg: 'bg-blue-500/10', color: 'text-blue-400',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
      </svg>
    ),
    title: 'Proof of Work',
    desc:  'Verify your coding skills via GitHub integration. Real code, real evidence, real jobs.',
    bg: 'bg-emerald-500/10', color: 'text-emerald-400',
  },
]

const STATS = [
  { value: '0 cost',   label: 'Open access for all' },
  { value: '24/7',    label: 'AI Mentor Availability' },
  { value: '30s',  label: 'To land your roadmap' },
  { value: '100%', label: 'Free Resource Selection' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen text-slate-200">

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden pt-36 pb-24 px-4 sm:px-6">
        {/* Animated Background Orbs */}
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent-600/20 blur-[120px] rounded-full animate-float pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/20 blur-[120px] rounded-full animate-float pointer-events-none" style={{ animationDelay: '-3s' }} />

        <div className="relative max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-8 animate-fade-in">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-500 animate-pulse" />
            Built for the next generation of engineers
          </div>

          <h1 className="font-display text-5xl sm:text-7xl font-extrabold text-white leading-[1.1] mb-8 animate-fade-up">
            Master your career <br />
            <span className="text-gradient">with AI Guidance.</span>
          </h1>

          <p className="text-slate-400 text-lg sm:text-xl max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-up" style={{ animationDelay: '0.1s' }}>
            The world's first <span className="text-white font-semibold">Zero-Cost Career Navigator</span>. Analyze gaps, get mentor-grade feedback, and master any role with free resources.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-up" style={{ animationDelay: '0.2s' }}>
            <Link to="/analyze" className="btn-primary text-base px-10 py-4 rounded-2xl w-full sm:w-auto shadow-xl shadow-accent-500/20">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
              </svg>
              Start Free Journey
            </Link>
            <Link to="/translator"
              className="btn-secondary w-full sm:w-auto px-10 py-4 rounded-2xl border-white/5 bg-white/5 hover:bg-white/10 transition-all font-display text-white">
              Resume Translator →
            </Link>
          </div>
        </div>
      </section>

      {/* ── Stats ──────────────────────────────────────────────────────── */}
      <section className="py-12 border-y border-white/5 bg-slate-900/40 backdrop-blur-sm relative z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
            {STATS.map(s => (
              <div key={s.label} className="flex flex-col items-center gap-1 text-center">
                <span className="font-display font-extrabold text-3xl text-white">{s.value}</span>
                <span className="text-slate-500 text-[10px] font-bold uppercase tracking-widest">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ───────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-32 relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-accent-500/5 blur-[80px] rounded-full pointer-events-none" />
        
        <div className="text-center mb-20">
          <p className="text-accent-400 text-xs font-bold uppercase tracking-[0.3em] mb-4">Core Intelligence</p>
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white tracking-tight">
            Stop Guessing. <span className="text-slate-500">Start Growing.</span>
          </h2>
        </div>

        <div className="grid sm:grid-cols-3 gap-8">
          {FEATURES.map((f, i) => (
            <div key={f.title} className="card p-8 group hover:border-accent-500/30 transition-all duration-300 animate-fade-up"
              style={{ animationDelay: `${i * 100}ms` }}>
              <div className={`w-14 h-14 rounded-2xl ${f.bg} ${f.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                {f.icon}
              </div>
              <h3 className="font-display font-bold text-slate-100 text-xl mb-3">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────────────────── */}
      <section className="py-32 px-4 sm:px-6 relative overflow-hidden">
        <div className="card max-w-5xl mx-auto p-12 sm:p-20 text-center relative overflow-hidden">
           <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5" />
           <div className="relative z-10">
             <h2 className="font-display text-4xl sm:text-6xl font-extrabold text-white mb-6">
                Ready to land <br className="sm:hidden" />
                <span className="text-gradient">your first role?</span>
             </h2>
             <p className="text-slate-400 mb-12 text-lg sm:text-xl max-w-xl mx-auto">
                Join thousands of freshers who used PathFinder AI to bridge their gaps and land their dream jobs.
             </p>
             <Link to="/analyze" className="btn-primary text-lg px-12 py-5 rounded-2xl shadow-2xl shadow-accent-500/30">
                Generate My Roadmap →
             </Link>
           </div>
        </div>
      </section>

      <footer className="py-12 border-t border-white/5 text-center">
         <p className="text-slate-600 text-xs uppercase tracking-widest font-bold">PathFinder AI · 2025</p>
      </footer>
    </div>
  )
}