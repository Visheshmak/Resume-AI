import { useEffect, useRef, useState } from "react";
import { motion, type Transition, type Variants } from "motion/react";

type InViewProps = {
  children: React.ReactNode;
  variants?: Variants;
  transition?: Transition;
  viewOptions?: IntersectionObserverInit & { margin?: string };
  className?: string;
};

const defaultVariants: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

function InView({ children, variants = defaultVariants, transition, viewOptions, className }: InViewProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    let fallbackTimer = window.setTimeout(() => setIsVisible(true), 120);
    const { margin, ...observerOptions } = viewOptions ?? {};
    const observer = new IntersectionObserver(([entry]) => {
      if (entry?.isIntersecting) {
        window.clearTimeout(fallbackTimer);
        setIsVisible(true);
        observer.disconnect();
      }
    }, { ...observerOptions, rootMargin: margin ?? observerOptions.rootMargin });
    observer.observe(element);
    return () => {
      window.clearTimeout(fallbackTimer);
      observer.disconnect();
    };
  }, [viewOptions]);

  return <motion.div ref={ref} className={className} initial="hidden" animate={isVisible ? "visible" : "hidden"} variants={variants} transition={transition}>{children}</motion.div>;
}

export type { InViewProps };
export { InView };
