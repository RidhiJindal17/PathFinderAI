import { useEffect, useState } from 'react';
import { useParams, useLocation, Link } from 'react-router-dom';
import { getReport } from '../api';
import MatchScore      from '../components/MatchScore';
import SkillChip       from '../components/SkillChip';
import BridgeSkillCard from '../components/BridgeSkillCard';
import WeekCard        from '../components/WeekCard';

// ── Section wrapper ──────────────────────────────────────────────────────────
function Section({ title, subtitle, children, id }) {
  return (
    <section id={id} className="mb-10">
      <div className="flex items-baseline gap-3 mb-4">
        <h2 className="section-title">{title}</h2>
        {subtitle && (
          <span className="text-sm text-slate-400">{subtitle}</span>
        )}
      </div>

      {children}
    </section>
  );
}

// ── Main ReportPage ──────────────────────────────────────────────────────────
export default function ReportPage() {
  const { reportId }   = useParams();
  const { state }      = useLocation();
  const [report,     setReport]     = useState(state?.report || null);
  const [loading,    setLoading]    = useState(!state?.report);
  const [error,      setError]      = useState('');

  useEffect(() => {
    if (!report && reportId) {
      setLoading(true);
      getReport(reportId)
        .then(setReport)
        .catch(err => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [reportId]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center pt-20">
      <div className="flex flex-col items-center gap-3">
        <svg className="w-8 h-8 text-navy-500 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <p className="text-slate-500 text-sm">Loading report…</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center pt-20 px-4">
      <div className="card p-8 max-w-sm w-full text-center">
        <p className="font-display text-xl font-bold text-navy-700 mb-2">Couldn't load report</p>
        <p className="text-slate-500 text-sm mb-6">{error}</p>
        <Link to="/analyze" className="btn-primary justify-center w-full">Try Again</Link>
      </div>
    </div>
  );

  if (!report) return null;

  const {
    resume_summary       = {},
    job_title            = '',
    match_score          = 0,
    matched_skills       = [],
    bridge_skills        = [],
    missing_skills       = [],
    missing_skills_detailed = [],
    resources            = [],
    skill_gap_percentage = 0,
    roadmap              = [],
    estimated_time       = '',
    confidence_score     = '',
    xai_explanations     = [],
    four_week_plan       = [],
    confidence_message   = '',
    github_portfolio     = null,
    created_at           = '',
    analysis_note        = '',
    final_summary        = '',
    suitable_roles       = [],
  } = report || {};

  const xaiMap = {};
  (xai_explanations || []).forEach(x => { xaiMap[x.skill] = x; });

  const dateStr = created_at
    ? new Date(created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    : '';

  return (
    <div className="min-h-screen pt-20 pb-16 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto">

        {/* ── Print / Back bar ───────────────────────────────────────────── */}
        <div className="flex items-center justify-between mb-6 print:hidden">
          <Link to="/analyze" className="btn-secondary text-sm px-4 py-2">
            ← New Analysis
          </Link>
          <button onClick={() => window.print()} className="btn-secondary text-sm px-4 py-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Download Report
          </button>
        </div>

        {/* ── Section A: Header card ─────────────────────────────────────── */}
        <div className="card p-6 sm:p-8 mb-8 animate-fade-up">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <MatchScore score={match_score} />
            <div className="flex-1 text-center sm:text-left">
              <p className="text-xs font-semibold text-accent-500 uppercase tracking-widest mb-1">
                PathFinder AI — Analysis Report
              </p>
              <h1 className="font-display text-2xl sm:text-3xl font-bold text-navy-700 mb-1">
                {resume_summary.name || 'Your Report'}
              </h1>
              <p className="text-slate-500 text-sm mb-3">
                Applying for: <span className="font-semibold text-navy-600">{job_title}</span>
              </p>
              {resume_summary.email && (
                <p className="text-xs text-slate-400 mb-1">{resume_summary.email}</p>
              )}
              {dateStr && (
                <p className="text-xs text-slate-400">Analyzed on {dateStr}</p>
              )}

              {/* Quick stats */}
              <div className="flex flex-wrap justify-center sm:justify-start gap-3 mt-4">
                {[
                  { label: 'Skills found',   val: resume_summary.skills?.length || 0 },
                  { label: 'Education',      val: resume_summary.education_count  || 0 },
                  { label: 'Experience',     val: resume_summary.experience_count || 0 },
                  { label: 'Projects',       val: resume_summary.projects_count   || 0 },
                ].map(s => (
                  <div key={s.label} className="bg-navy-50 rounded-xl px-3 py-2 text-center min-w-[60px]">
                    <p className="font-bold text-navy-700 text-lg leading-none">{s.val}</p>
                    <p className="text-xs text-navy-400 mt-0.5">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Section B: Skill Overview ──────────────────────────────────── */}
        <Section title="Expert Skill Analysis" id="skills">
          <div className="grid sm:grid-cols-2 gap-4 mb-6">
            <div className="card p-5 group hover:border-emerald-500/30 transition-all duration-300">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
                <h3 className="font-display font-bold text-slate-100">Matched Skills ({matched_skills.length})</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {(matched_skills || []).length > 0
                  ? (matched_skills || []).map(s => <SkillChip key={s} skill={s} variant="green" />)
                  : <p className="text-sm text-slate-400 italic">No direct matches found yet.</p>
                }
              </div>
            </div>

            <div className="card p-5 group hover:border-rose-500/30 transition-all duration-300">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-rose-500/10 flex items-center justify-center text-rose-500">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                </div>
                <h3 className="font-display font-bold text-slate-100">Missing Critical Skills ({missing_skills_detailed.length})</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {analysis_note && (
                  <div className="w-full mb-4 p-4 rounded-xl bg-accent-500/10 border border-accent-500/20 flex gap-3">
                    <svg className="w-5 h-5 text-accent-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <p className="text-sm text-slate-300 italic">{analysis_note}</p>
                  </div>
                )}

                {(missing_skills_detailed || []).length > 0 ? (
                  (missing_skills_detailed || []).map(m => (
                    <SkillChip key={m.skill} skill={m.skill} variant={m.priority?.toLowerCase() || 'high'} />
                  ))
                ) : match_score > 80 ? (
                  <p className="text-sm text-emerald-400 italic">Perfect match! No critical missing skills found.</p>
                ) : (
                  <div className="w-full p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <p className="text-sm text-amber-500 italic">No direct gaps detected, but your overall score ({match_score}%) is low. Consider refining your resume to match the job requirements more closely.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Section>

        {/* ── Section C: Mentor Feedback (NEW) ─────────────────────────────── */}
        {(missing_skills_detailed || []).length > 0 && (
          <Section title="Why you are not selected" subtitle="Candid feedback from our AI Mentor">
            <div className="card border-l-4 border-rose-500 p-6 bg-rose-500/5">
              <div className="space-y-6">
                {(missing_skills_detailed || []).map((item, idx) => (
                  <div key={idx} className="flex gap-4 group">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-rose-500/20 text-rose-500 flex items-center justify-center font-bold text-sm">
                      !
                    </div>
                    <div>
                      <h4 className="font-display font-bold text-rose-400 text-base mb-1 flex items-center gap-2">
                        Lack of {item.skill} proficiency
                        <SkillChip skill={item.priority} variant={item.priority?.toLowerCase()} />
                      </h4>
                      <p className="text-slate-300 text-sm leading-relaxed mb-2">
                        {item.why_important}
                      </p>
                      <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-800">
                        <p className="text-xs text-rose-300/80 font-medium uppercase tracking-wider mb-1">Impact on Selection</p>
                        <p className="text-sm text-slate-400 italic">
                          "{item.impact_if_missing}"
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Section>
        )}

        {/* ── Section New: Suitable Roles ───────────────────────────────── */}
        {(suitable_roles || []).length > 0 && (
          <Section title="You Are Currently Suitable For" subtitle="Based on your current skills" id="suitable-roles">
            <div className="card p-6 bg-emerald-500/5 border-emerald-500/20">
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {(suitable_roles || []).map((role, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 rounded-xl bg-slate-900/50 border border-emerald-500/10 hover:border-emerald-500/30 transition-all group">
                    <div className="w-6 h-6 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500 flex-shrink-0">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className="text-slate-200 font-medium">{role}</span>
                  </div>
                ))}
              </div>
            </div>
          </Section>
        )}

        {/* ── Section D: Recommended Learning Path (UPGRADED) ────────────────── */}
        {(resources || []).length > 0 && (
          <Section title="Recommended Learning Path" subtitle="Curated resources and estimated time to completion">
            <div className="grid md:grid-cols-2 gap-4">
              {(resources || []).map((skillGroup, idx) => (
                <div key={idx} className="card p-5 hover:translate-y-[-4px] transition-all duration-300">
                  <div className="flex items-start justify-between mb-4">
                    <h4 className="font-display font-bold text-slate-100 text-lg flex items-center gap-2">
                      <span className="w-1.5 h-6 bg-accent-500 rounded-full" />
                      {skillGroup.skill}
                    </h4>
                    <span className="text-[10px] font-bold text-accent-400 bg-accent-500/10 px-2 py-1 rounded-md border border-accent-500/20 uppercase tracking-tight">
                      {skillGroup.estimated_time || '2-4 weeks'}
                    </span>
                  </div>
                  <div className="space-y-3">
                    {(skillGroup.resources || []).map((link, lIdx) => (
                      <a 
                        key={lIdx}
                        href={link.url} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className={`flex items-center gap-3 p-3 rounded-xl border transition-all group ${
                          link.type === 'video' ? 'bg-red-500/10 border-red-500/20 hover:bg-red-500/20' :
                          link.type === 'article' ? 'bg-blue-500/10 border-blue-500/20 hover:bg-blue-500/20' :
                          'bg-emerald-500/10 border-emerald-500/20 hover:bg-emerald-500/20'
                        }`}
                      >
                        <div className={
                          link.type === 'video' ? 'text-red-500' :
                          link.type === 'article' ? 'text-blue-500' :
                          'text-emerald-500'
                        }>
                          {link.type === 'video' && <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/></svg>}
                          {link.type === 'article' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>}
                          {link.type === 'docs' && <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
                        </div>
                        <div className="flex-1 text-sm font-medium text-slate-200">{link.title}</div>
                        <svg className="w-4 h-4 text-slate-500 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                      </a>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* ── Section E: Career Roadmap ───────────────────────────── */}
        {roadmap?.length > 0 && (
          <Section title="Your Success Roadmap" id="roadmap">
            <div className="relative pl-8 space-y-8 before:content-[''] before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {(roadmap || []).map((stage, idx) => (
                <div key={idx} className="relative group">
                  <div className="absolute left-[-26px] top-1.5 w-4 h-4 rounded-full bg-slate-900 border-2 border-accent-500 ring-4 ring-slate-950 flex items-center justify-center transition-all group-hover:scale-125" />
                  <div className="card p-6 border-l-0 group-hover:border-accent-500/30 transition-all transition-duration-300">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold text-accent-400 uppercase tracking-widest">{stage.duration}</span>
                          <span className="w-1 h-1 rounded-full bg-slate-600" />
                          <span className="text-xs font-semibold text-slate-500 uppercase">{stage.stage} Level</span>
                        </div>
                        <h3 className="font-display font-bold text-slate-100 text-xl">{stage.stage} Strategy</h3>
                      </div>
                      <div className="bg-slate-900/80 px-4 py-2 rounded-xl border border-slate-800 text-center">
                        <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Timeline</p>
                        <p className="text-sm font-display font-bold text-accent-400">{stage.duration}</p>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {(stage.skills || []).map(skill => (
                        <span key={skill} className="px-3 py-1.5 rounded-lg bg-navy-900/50 border border-navy-700/50 text-slate-300 text-sm font-medium">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {estimated_time && (
              <div className="card mt-8 p-6 bg-accent-500/5 border-accent-500/20 text-center">
                <p className="text-slate-400 text-sm mb-1 uppercase tracking-widest font-bold">The Big Picture</p>
                <h3 className="font-display font-bold text-accent-400 text-xl">
                  {estimated_time}
                </h3>
              </div>
            )}
          </Section>
        )}

        {/* ── Section F: GitHub Portfolio ────────────────────────────────── */}
        {github_portfolio && (
          <Section title="Professional Proof of Work" id="github">
            <div className="card p-6 group hover:border-blue-500/30 transition-all duration-300">
              {/* Profile row */}
              <div className="flex items-center gap-4 mb-5 pb-5 border-b border-white/5">
                {github_portfolio.profile?.avatar_url && (
                  <div className="relative">
                    <img
                      src={github_portfolio.profile.avatar_url}
                      alt="GitHub avatar"
                      className="w-16 h-16 rounded-2xl border-2 border-slate-700 group-hover:border-blue-500/50 transition-colors"
                    />
                    <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-slate-900 rounded-full flex items-center justify-center border border-slate-700">
                      <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.041-1.412-4.041-1.412-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.382 1.235-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.839 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                    </div>
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-display font-bold text-slate-100 text-lg">
                      {github_portfolio.profile?.name || github_portfolio.profile?.login}
                    </p>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                      github_portfolio.activity_level === 'active'   ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : github_portfolio.activity_level === 'moderate' ? 'bg-accent-500/10 text-accent-400 border border-accent-500/20'
                      : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                    }`}>
                      {github_portfolio.activity_level} contributor
                    </span>
                  </div>
                  {github_portfolio.profile?.bio && (
                    <p className="text-sm text-slate-400 mt-0.5 italic">{github_portfolio.profile.bio}</p>
                  )}
                  <div className="flex gap-4 mt-2">
                    <span className="text-xs text-slate-500 font-medium">⭐ {github_portfolio.total_stars?.toLocaleString()}</span>
                    <span className="text-xs text-slate-500 font-medium">📂 {github_portfolio.repo_count}</span>
                    <span className="text-xs text-slate-500 font-medium">🔗 {github_portfolio.profile?.followers?.toLocaleString()} followers</span>
                  </div>
                </div>
                <a href={github_portfolio.profile?.html_url} target="_blank" rel="noopener noreferrer"
                  className="btn-secondary text-xs px-3 py-2 flex-shrink-0 hidden sm:inline-flex group-hover:bg-blue-600 transition-colors">
                  View Profile
                </a>
              </div>

              {/* Skill evidence */}
              {github_portfolio.skill_evidence?.length > 0 && (
                <div className="mb-6">
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Skill Verification via GitHub</p>
                  <div className="flex flex-wrap gap-2">
                    {github_portfolio.skill_evidence.map(lang => (
                      <SkillChip key={lang} skill={lang} variant="blue" />
                    ))}
                  </div>
                </div>
              )}

              {/* Top repos */}
              <div className="grid sm:grid-cols-3 gap-3">
                {github_portfolio.top_repos?.slice(0, 3).map(repo => (
                  <a key={repo.name} href={repo.html_url} target="_blank" rel="noopener noreferrer"
                    className="flex flex-col p-4 rounded-xl bg-slate-900/50 border border-white/5 hover:border-accent-500/30 transition-all group/repo">
                    <p className="font-bold text-slate-200 text-sm truncate mb-1 group-hover/repo:text-accent-400">{repo.name}</p>
                    <div className="mt-auto flex items-center justify-between">
                      <span className="text-[10px] text-slate-500 font-bold uppercase">{repo.language || 'Code'}</span>
                      <span className="text-[10px] text-slate-400 flex items-center gap-1">⭐ {repo.stars}</span>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          </Section>
        )}


        {/* ── Section H: AI Mentor Conclusion ─────────────────────────────── */}
        {(final_summary || confidence_score || confidence_message) && (
          <section className="mb-12 animate-fade-up" style={{ animationDelay: '0.4s' }}>
            <div className="card p-8 bg-gradient-to-r from-navy-900 to-indigo-950 border-accent-500/20 relative group overflow-hidden">
              <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-accent-500/5 rounded-full blur-3xl pointer-events-none" />
              <div className="absolute top-4 right-6 text-accent-500/10 group-hover:text-accent-500/20 transition-colors">
                <svg className="w-24 h-24" fill="currentColor" viewBox="0 0 24 24"><path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/></svg>
              </div>
              
              <div className="relative z-10">
                <p className="text-xs font-bold text-accent-500 uppercase tracking-[0.3em] mb-4">Mentor Verdict</p>
                <div className="prose prose-invert max-w-none">
                  <p className="font-display text-xl text-slate-100 leading-relaxed font-medium mb-8 border-l-2 border-accent-500 pl-6 italic">
                    "{final_summary || confidence_score || confidence_message}"
                  </p>
                </div>
                
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent-400 to-accent-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-accent-500/20 ring-4 ring-white/5">
                    CM
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-100 leading-none">AI Career Mentor</p>
                    <p className="text-xs text-slate-500 mt-1.5 font-medium uppercase tracking-wider">Expert Insights</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ── Bottom actions ─────────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row gap-3 print:hidden">
          <Link to="/analyze" className="btn-secondary flex-1 justify-center">
            ← Analyze Another
          </Link>
          <Link to="/translator" className="btn-secondary flex-1 justify-center border-accent-500/30 text-accent-400 hover:bg-accent-500/10">
            Improve Resume →
          </Link>
          <button onClick={() => window.print()} className="btn-primary flex-1 justify-center">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Download PDF
          </button>
        </div>
      </div>
    </div>
  );
}