/**
 * SkillChip.jsx — colored pill for a skill name
 * variant: "green" | "blue" | "orange" | "gray" | "red"
 */
export default function SkillChip({ skill, variant = 'blue' }) {
  const styles = {
    green:  'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]',
    blue:   'bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]',
    orange: 'bg-accent-500/10 text-accent-400 border border-accent-500/20 shadow-[0_0_15px_rgba(139,92,246,0.1)]',
    gray:   'bg-slate-700/30 text-slate-400 border border-slate-700/50',
    red:    'bg-red-500/10 text-red-400 border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]',
    rose:   'bg-rose-500/10 text-rose-400 border border-rose-500/20 shadow-[0_0_15px_rgba(244,63,94,0.1)]',
    high:   'bg-red-500/10 text-red-500 border border-red-500/30 font-bold',
    medium: 'bg-amber-500/10 text-amber-500 border border-amber-500/30 font-bold',
    low:    'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 font-bold',
  };

  return (
    <span className={`chip ${styles[variant] || styles.blue}`}>
      {skill}
    </span>
  );
}