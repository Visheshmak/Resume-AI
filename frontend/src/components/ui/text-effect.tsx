import { motion } from "framer-motion";
import type { HTMLAttributes, ReactNode } from "react";

type TextEffectProps = HTMLAttributes<HTMLSpanElement> & {
  children: ReactNode;
  per?: "word" | "char";
  preset?: "blur" | "fade" | "slide";
  delay?: number;
  speedReveal?: number;
};

const presets = {
  blur: {
    hidden: { opacity: 0, filter: "blur(10px)", y: 8 },
    visible: { opacity: 1, filter: "blur(0px)", y: 0 },
  },
  fade: {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  },
  slide: {
    hidden: { opacity: 0, y: "0.7em" },
    visible: { opacity: 1, y: 0 },
  },
} as const;

export function TextEffect({
  children,
  per = "word",
  preset = "fade",
  delay = 0,
  speedReveal = 0.08,
  ...props
}: TextEffectProps) {
  const text = String(children);
  const parts = per === "char" ? Array.from(text) : text.split(/(\s+)/);
  const variants = presets[preset];

  return (
    <span {...props}>
      {parts.map((part, index) => {
        if (/^\s+$/.test(part)) return part;

        return (
          <motion.span
            key={`${part}-${index}`}
            aria-hidden="true"
            className="inline-block"
            variants={variants}
            initial="hidden"
            animate="visible"
            transition={{
              duration: 0.55,
              delay: delay + index * speedReveal,
              ease: [0.22, 1, 0.36, 1],
            }}
          >
            {part}
          </motion.span>
        );
      })}
      <span className="sr-only">{text}</span>
    </span>
  );
}
