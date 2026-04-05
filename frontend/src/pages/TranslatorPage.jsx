import { useState } from 'react';
import { translateText } from '../api';

const EXAMPLES = [
  "I fixed my neighbour's computer when it was slow",
  "Helped my college run the annual cultural fest",
  "Made a website for my dad's shop",
  "I used to teach kids in my village how to use computers",
];

export default function TranslatorPage() {
  const [inputText, setInputText] = useState('');
  const [result,    setResult]    = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState('');
  const [copied,    setCopied]    = useState(false);

  async function handleTranslate() {
    console.log('[DEBUG] handleTranslate triggered. Input:', inputText);
    if (!inputText || inputText.trim().length === 0) {
      console.log('[DEBUG] Input is empty/whitespace. Aborting.');
      return;
    }
    setLoading(true); setError(''); setResult(null);
    try {
      console.log('[DEBUG] Calling translateText API...');
      const proData = await translateText(inputText);
      console.log('[DEBUG] Translation result received:', proData);
      setResult(proData);
    } catch (err) {
      console.error('[DEBUG] handleTranslate fatal error:', err);
      if (err.response) {
        console.error('[DEBUG] API error response:', err.response.data);
        setError(`API error: ${err.response.data.detail || 'The server returned an error.'}`);
      } else if (err.request) {
        console.error('[DEBUG] API network error:', err.request);
        setError('Network error: Could not reach the backend server.');
      } else {
        setError(`Error: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    if (!result) return;
    navigator.clipboard.writeText(result.polished_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function loadExample(ex) {
    setInputText(ex);
    setResult(null);
    setError('');
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6 relative flex flex-col justify-center items-center">
      {/* Dynamic Background Glow Elements */}
      <div className="absolute top-20 left-1/4 w-72 h-72 bg-violet-600/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-20 right-1/4 w-80 h-80 bg-cyan-600/20 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-2xl w-full mx-auto relative z-10">

        {/* Header */}
        <div className="text-center mb-12 animate-fade-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl
                          bg-gradient-to-br from-violet-600 to-indigo-600 shadow-lg shadow-indigo-500/25 
                          text-white mb-6 mx-auto animate-float border border-white/10 relative">
            <div className="absolute inset-0 bg-white/20 rounded-2xl opacity-0 hover:opacity-100 transition-opacity"></div>
            <svg className="w-8 h-8 relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </div>
          <p className="text-violet-400 text-sm font-bold uppercase tracking-[0.2em] mb-3">AI-Powered Magic v2.0</p>
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
            Corporate <span className="text-gradient">Translator</span>
          </h1>
          <p className="text-slate-400 text-lg max-w-md mx-auto leading-relaxed">
            Generate high-impact, ATS-optimized resume bullet points that command attention from recruiters.
          </p>
        </div>

        {/* How it works strip */}
        <div className="grid grid-cols-3 gap-4 mb-8 animate-fade-up" style={{ animationDelay: '100ms' }}>
          {[
            { icon: '✍️', title: 'Action Verbs', label: 'Strong openers' },
            { icon: '📈', title: 'Keywords', label: 'ATS-Optimized' },
            { icon: '🎯', title: 'Impact', label: 'Result driven' },
          ].map((s, i) => (
            <div key={i} className="card card-hover p-4 text-center cursor-default">
              <span className="text-3xl block mb-2 drop-shadow-md">{s.icon}</span>
              <p className="text-sm font-semibold text-slate-200">{s.title}</p>
              <p className="text-xs text-slate-400 mt-1 leading-snug">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Main card */}
        <div className="card p-8 space-y-6 animate-fade-up" style={{ animationDelay: '200ms' }}>

          {/* Examples */}
          <div>
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
              Try a typical informal description
            </p>
            <div className="flex flex-wrap gap-2.5">
              {EXAMPLES.map(ex => (
                <button
                  key={ex}
                  onClick={() => loadExample(ex)}
                  className="text-xs font-medium bg-slate-800/50 text-slate-300 border border-slate-700/50
                             px-4 py-2 rounded-xl hover:bg-violet-600/20 hover:border-violet-500/30 hover:text-violet-200
                             transition-all duration-200 text-left shadow-sm"
                >
                  {ex.length > 40 ? ex.slice(0, 40) + '…' : ex}
                </button>
              ))}
            </div>
          </div>

          <div className="border-t border-slate-700/50" />

          {/* Input */}
          <div className="relative group">
            <label className="form-label text-slate-400">Describe what you did</label>
            <textarea
              autoFocus
              id="informal_text"
              name="informal_text"
              value={inputText}
              onChange={e => {
                const val = e.target.value;
                setInputText(val);
              }}
              rows={4}
              placeholder="e.g. 'I was in charge of our college tech team' or 'I made a discord bot for my friend'"
              className="input-field resize-none shadow-inner"
            />
          </div>

          {/* Submit */}
          <button
            type="button"
            onClick={handleTranslate}
            disabled={loading || !inputText || inputText.length === 0}
            className="btn-primary w-full justify-center py-4 text-lg mt-2"
          >
            {loading ? (
              <>
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Optimizing for Recruiters...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Transform to High-Impact
              </>
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-3 p-4 bg-red-950/40 border border-red-900/50 rounded-xl animate-fade-in backdrop-blur-sm">
              <p className="text-red-300 text-sm font-medium leading-relaxed">{error}</p>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="bg-gradient-to-br from-emerald-950/40 to-teal-950/40 border border-emerald-800/30 rounded-2xl p-6 animate-fade-in shadow-lg shadow-emerald-900/10">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">✨</span>
                    <p className="text-xs font-bold text-emerald-400 uppercase tracking-widest">
                      Polished Achievement
                    </p>
                  </div>
                  {result.tone && (
                    <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-[10px] font-bold text-emerald-400/80 uppercase tracking-tighter">
                      {result.tone} tone
                    </span>
                  )}
                </div>
                <button
                  onClick={handleCopy}
                  className="inline-flex items-center gap-1.5 text-xs font-bold
                             bg-emerald-900/30 border border-emerald-700/50 text-emerald-300
                             px-3.5 py-1.5 rounded-lg hover:bg-emerald-800/50 hover:text-emerald-200 transition-all shadow-sm"
                >
                  {copied ? 'Copied!' : 'Copy to Resume'}
                </button>
              </div>
              <p className="text-emerald-100 text-lg leading-relaxed font-medium bg-emerald-950/30 p-4 rounded-xl border border-emerald-800/40 shadow-inner">
                {result.polished_text}
              </p>

              <div className="mt-5 pt-5 border-t border-emerald-800/30 flex items-center gap-6 mb-6">
                <div>
                   <p className="text-[10px] text-emerald-400/50 font-bold uppercase tracking-wider mb-1">Keywords</p>
                   <p className="text-xs text-emerald-200/60 font-medium">Inferred from domain</p>
                </div>
                <div>
                   <p className="text-[10px] text-emerald-400/50 font-bold uppercase tracking-wider mb-1">Impact Tier</p>
                   <p className="text-xs text-emerald-200/60 font-medium">High Impact</p>
                </div>
                <div>
                   <p className="text-[10px] text-emerald-400/50 font-bold uppercase tracking-wider mb-1">ATS Check</p>
                   <p className="text-xs text-emerald-200/60 font-medium">Optimized ✓</p>
                </div>
              </div>

              <div className="pt-5 border-t border-emerald-800/30">
                <p className="text-xs text-emerald-400/80 font-bold mb-2 uppercase tracking-wide">💡 Pro Tips:</p>
                <ul className="text-sm text-emerald-200/80 space-y-2">
                  <li className="flex items-center gap-2"><span className="text-emerald-500">•</span> Use it directly in your resume Work Experience</li>
                  <li className="flex items-center gap-2"><span className="text-emerald-500">•</span> Add quantifiable numbers if you know them (e.g. "3 clients")</li>
                  <li className="flex items-center gap-2"><span className="text-emerald-500">•</span> Mirror this style on your LinkedIn profile</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Info cards */}
        <div className="grid sm:grid-cols-2 gap-5 mt-10 animate-fade-up" style={{ animationDelay: '300ms' }}>
          <div className="card p-5">
            <p className="font-bold text-violet-300 text-sm mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              What it does well
            </p>
            <ul className="text-sm text-slate-400 space-y-2.5">
              <li className="flex items-center gap-2"><span className="text-indigo-400">✓</span> Adds strong action verbs</li>
              <li className="flex items-center gap-2"><span className="text-indigo-400">✓</span> Removes casual pronouns (ATS-friendly)</li>
              <li className="flex items-center gap-2"><span className="text-indigo-400">✓</span> Estimates impact with ~ markers</li>
              <li className="flex items-center gap-2"><span className="text-indigo-400">✓</span> Keeps it perfectly concise</li>
            </ul>
          </div>
          <div className="card p-5">
            <p className="font-bold text-cyan-300 text-sm mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
              Tips for better results
            </p>
            <ul className="text-sm text-slate-400 space-y-2.5">
              <li className="flex items-center gap-2"><span className="text-cyan-400/70">💡</span> Mention the outcome</li>
              <li className="flex items-center gap-2"><span className="text-cyan-400/70">💡</span> Include actual numbers</li>
              <li className="flex items-center gap-2"><span className="text-cyan-400/70">💡</span> Translate one task at a time</li>
              <li className="flex items-center gap-2"><span className="text-cyan-400/70">💡</span> Always proofread</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}