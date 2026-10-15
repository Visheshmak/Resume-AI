import { motion } from "framer-motion";

type ScoreRingProps = { label: string; score?: number; tone?: "lime" | "teal" | "amber"; detail?: string };

export function ScoreRing({ label, score, tone = "lime", detail }: ScoreRingProps) {
  const hasScore = typeof score === "number";
  const radius = 35;
  const circumference = 2 * Math.PI * radius;
  const progress = hasScore ? circumference - (score / 100) * circumference : circumference;

  return (
    <div className="score-ring-card">
      <div className={`score-ring ${tone}`}>
        <svg viewBox="0 0 88 88" aria-hidden="true">
          <circle className="score-track" cx="44" cy="44" r={radius} />
          {hasScore && <motion.circle className="score-progress" cx="44" cy="44" r={radius} initial={{ strokeDashoffset: circumference }} animate={{ strokeDashoffset: progress }} transition={{ duration: 1.2, ease: "easeOut" }} style={{ strokeDasharray: circumference }} />}
        </svg>
        <span>{hasScore ? `${score}` : "--"}</span>
      </div>
      <div><strong>{label}</strong><small>{detail ?? (hasScore ? "Evidence-backed" : "Awaiting analysis")}</small></div>
    </div>
  );
}
