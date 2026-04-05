import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitAnalysis } from '../api';
import LoadingSteps from '../components/LoadingSteps';

const MAX_FILE_SIZE_MB = 5;
const MAX_FILE_BYTES   = MAX_FILE_SIZE_MB * 1024 * 1024;
const MIN_JD_CHARS     = 100;

// Progress simulation: approximate which step is running based on elapsed time
function useProgressSimulator(isLoading) {
  const [currentStep, setCurrentStep] = useState(0);
  const intervalRef = useRef(null);

  const start = useCallback(() => {
    setCurrentStep(0);
    let step = 0;
    const durations = [3000, 5000, 15000, 4000]; // ms per step
    let elapsed = 0;

    const tick = () => {
      elapsed += 500;
      if (elapsed >= durations[step] && step < durations.length - 1) {
        step++;
        setCurrentStep(step);
        elapsed = 0;
      }
    };
    intervalRef.current = setInterval(tick, 500);
  }, []);

  const stop = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
  }, []);

  return { currentStep, start, stop };
}

export default function AnalyzePage() {
  const navigate = useNavigate();

  // Form state
  const [pdfFile,        setPdfFile]        = useState(null);
  const [jobTitle,       setJobTitle]       = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [githubUsername, setGithubUsername] = useState('');

  // UI state
  const [isDragging,   setIsDragging]   = useState(false);
  const [isLoading,    setIsLoading]    = useState(false);
  const [error,        setError]        = useState('');
  const [fieldErrors,  setFieldErrors]  = useState({});

  const fileInputRef = useRef(null);
  const { currentStep, start: startProgress, stop: stopProgress } = useProgressSimulator(isLoading);

  // ── File handlers ──────────────────────────────────────────────────────────
  function validateFile(file) {
    if (!file) return 'Please select a file.';
    if (!file.name.toLowerCase().endsWith('.pdf')) return 'Only PDF files are accepted.';
    if (file.size > MAX_FILE_BYTES) return `File must be under ${MAX_FILE_SIZE_MB} MB. Yours is ${(file.size / 1024 / 1024).toFixed(1)} MB.`;
    return null;
  }

  function handleFileSelect(file) {
    const err = validateFile(file);
    if (err) {
      setFieldErrors(prev => ({ ...prev, file: err }));
      setPdfFile(null);
    } else {
      setFieldErrors(prev => ({ ...prev, file: null }));
      setPdfFile(file);
    }
  }

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileSelect(file);
  }, []);

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = () => setIsDragging(false);

  // ── Form validation ────────────────────────────────────────────────────────
  function validate() {
    const errs = {};
    if (!pdfFile)                                   errs.file = 'Please upload your resume PDF.';
    if (!jobTitle.trim())                            errs.jobTitle = 'Job title is required.';
    if (jobDescription.trim().length < MIN_JD_CHARS) errs.jobDesc = `Job description must be at least ${MIN_JD_CHARS} characters. Currently ${jobDescription.trim().length}.`;
    return errs;
  }

  // ── Submit ─────────────────────────────────────────────────────────────────
  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    const errs = validate();
    if (Object.keys(errs).length) { setFieldErrors(errs); return; }
    setFieldErrors({});

    setIsLoading(true);

    // 1. Check if backend is alive
    const { checkBackendStatus } = await import('../api');
    const isAlive = await checkBackendStatus();
    if (!isAlive) {
      setIsLoading(false);
      setError('Backend server not running. Please start FastAPI on port 8000.');
      return;
    }

    const formData = new FormData();
    formData.append('resume_file',    pdfFile);
    formData.append('job_description', jobDescription.trim());
    formData.append('job_title',       jobTitle.trim());
    if (githubUsername.trim()) formData.append('github_username', githubUsername.trim());

    // Debug log
    console.log('[Frontend] Prepared FormData:', {
      file: pdfFile.name,
      title: jobTitle,
      desc: jobDescription.substring(0, 50) + '...',
      github: githubUsername
    });

    startProgress();

    try {
      const report = await submitAnalysis(formData);
      console.log('[Frontend] Received report_id:', report.report_id);
      stopProgress();
      navigate(`/report/${report.report_id}`, { state: { report } });
    } catch (err) {
      console.error('[Frontend] Submit error:', err);
      stopProgress();
      setError(err.message || 'Analysis failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4 pt-20 pb-10">
        <div className="card p-10 max-w-md w-full text-center relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-accent-500 to-transparent animate-pulse" />
          
          <div className="w-20 h-20 rounded-3xl bg-accent-500/10 flex items-center justify-center mx-auto mb-6 relative">
            <div className="absolute inset-0 bg-accent-500/20 rounded-3xl animate-ping" />
            <svg className="w-10 h-10 text-accent-400 relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.456-2.455L18 2.25l.259 1.036a3.375 3.375 0 002.455 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.455zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
            </svg>
          </div>

          <h2 className="font-display font-bold text-2xl text-slate-100 mb-2">Generating Your Career Roadmap</h2>
          <p className="text-slate-400 text-sm mb-8 leading-relaxed">
            Our AI Mentor is analyzing the skill gaps and selecting the best free resources for your journey…
          </p>
          
          <div className="bg-slate-900/50 rounded-2xl p-6 border border-white/5 text-left mb-4">
             <LoadingSteps currentStep={currentStep} />
          </div>
          
          <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mt-4">
             Step {currentStep + 1} of 4: {['Parsing Knowledge', 'Mapping Skill Gaps', 'Generating Mentor Feedback', 'Finalizing Roadmap'][currentStep]}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10 animate-fade-up">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-500/10 border border-accent-500/20 text-accent-400 text-[10px] font-bold uppercase tracking-widest mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-500 animate-pulse" />
            AI Mentor Mode Active
          </div>
          <h1 className="font-display text-3xl sm:text-5xl font-bold text-white mb-4 tracking-tight">
            AI Career Navigator
          </h1>
          <p className="text-slate-400 text-lg max-w-lg mx-auto leading-relaxed">
            Upload your resume and target role. We'll identify your gaps and build a <span className="text-white font-semibold">bespoke learning journey</span>.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 animate-fade-up animate-delay-100">

          {/* ── Step 1: PDF Upload ─────────────────────────────────────── */}
          <div className="card p-6">
            <label className="form-label">
              <span className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-navy-700 text-white text-xs flex items-center justify-center font-bold">1</span>
                Resume PDF
              </span>
            </label>

            <div
              onClick={() => fileInputRef.current?.click()}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              className={`mt-2 border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer
                          transition-all duration-200 select-none
                          ${isDragging
                              ? 'border-accent-400 bg-accent-50'
                              : pdfFile
                                ? 'border-emerald-400 bg-emerald-50'
                                : fieldErrors.file
                                  ? 'border-red-300 bg-red-50'
                                  : 'border-slate-200 bg-slate-50 hover:border-navy-300 hover:bg-navy-50'
                          }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={e => handleFileSelect(e.target.files?.[0])}
              />

              {pdfFile ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className="font-semibold text-emerald-700 text-sm">{pdfFile.name}</p>
                  <p className="text-emerald-500 text-xs">{(pdfFile.size / 1024).toFixed(0)} KB · Click to change</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="w-10 h-10 rounded-xl bg-navy-100 flex items-center justify-center">
                    <svg className="w-5 h-5 text-navy-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <p className="text-sm font-semibold text-navy-700">Drop your PDF here</p>
                  <p className="text-xs text-slate-400">or click to browse · Max {MAX_FILE_SIZE_MB} MB</p>
                </div>
              )}
            </div>
            {fieldErrors.file && <p className="text-red-500 text-xs mt-1.5">{fieldErrors.file}</p>}
          </div>

          {/* ── Step 2: Job Title ──────────────────────────────────────── */}
          <div className="card p-6">
            <label className="form-label">
              <span className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-navy-700 text-white text-xs flex items-center justify-center font-bold">2</span>
                Job Title
              </span>
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={e => setJobTitle(e.target.value)}
              placeholder="e.g. React Frontend Developer"
              className={`input-field mt-2 ${fieldErrors.jobTitle ? 'border-red-300 focus:ring-red-300' : ''}`}
            />
            {fieldErrors.jobTitle && <p className="text-red-500 text-xs mt-1.5">{fieldErrors.jobTitle}</p>}
          </div>

          {/* ── Step 3: Job Description ────────────────────────────────── */}
          <div className="card p-6">
            <label className="form-label">
              <span className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-navy-700 text-white text-xs flex items-center justify-center font-bold">3</span>
                Job Description
              </span>
            </label>
            <textarea
              value={jobDescription}
              onChange={e => setJobDescription(e.target.value)}
              rows={7}
              placeholder="Paste the full job description here. Include requirements, responsibilities, and skills needed…"
              className={`input-field mt-2 resize-none ${fieldErrors.jobDesc ? 'border-red-300 focus:ring-red-300' : ''}`}
            />
            <div className="flex items-center justify-between mt-1.5">
              {fieldErrors.jobDesc
                ? <p className="text-red-500 text-xs">{fieldErrors.jobDesc}</p>
                : <p className="text-xs text-slate-400">Minimum {MIN_JD_CHARS} characters for accurate analysis</p>
              }
              <p className={`text-xs font-mono flex-shrink-0 ml-2 ${
                jobDescription.trim().length >= MIN_JD_CHARS ? 'text-emerald-500' : 'text-slate-400'
              }`}>
                {jobDescription.trim().length} chars
              </p>
            </div>
          </div>

          {/* ── Step 4: GitHub (optional) ──────────────────────────────── */}
          <div className="card p-6">
            <label className="form-label">
              <span className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-slate-300 text-white text-xs flex items-center justify-center font-bold">4</span>
                GitHub Username
                <span className="text-xs font-normal text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">Optional</span>
              </span>
            </label>
            <p className="text-xs text-slate-400 mb-2">Adds portfolio verification — shows which languages you've actually coded in.</p>
            <div className="relative mt-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-mono text-sm select-none">
                github.com/
              </span>
              <input
                type="text"
                value={githubUsername}
                onChange={e => setGithubUsername(e.target.value)}
                placeholder="yourusername"
                className="input-field pl-[6.5rem]"
              />
            </div>
          </div>

          {/* ── Error banner ───────────────────────────────────────────── */}
          {error && (
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl">
              <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <p className="text-red-700 text-sm font-semibold">Analysis failed</p>
                <p className="text-red-600 text-sm mt-0.5">{error}</p>
              </div>
              <button type="button" onClick={() => setError('')}
                className="text-red-400 hover:text-red-600 flex-shrink-0">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}

          {/* ── Submit ─────────────────────────────────────────────────── */}
          <button type="submit" className="btn-primary w-full text-base py-4 justify-center rounded-2xl shadow-glow">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            Analyze My Profile
          </button>

          <p className="text-center text-xs text-slate-400">
            Your resume is processed in memory and never stored permanently.
          </p>
        </form>
      </div>
    </div>
  );
}