import { createContext, useContext, useId, useState } from "react";
import { AnimatePresence, motion, type Transition, type Variants } from "motion/react";
import { createPortal } from "react-dom";
import { cn } from "../../lib/utils";

type MorphingDialogContextValue = {
  open: boolean;
  setOpen: (open: boolean) => void;
  id: string;
};

const MorphingDialogContext = createContext<MorphingDialogContextValue | undefined>(undefined);

function useMorphingDialog() {
  const context = useContext(MorphingDialogContext);
  if (!context) throw new Error("MorphingDialog components must be used inside MorphingDialog.");
  return context;
}

type MorphingDialogProps = {
  children: React.ReactNode;
  transition?: Transition;
};

function MorphingDialog({ children }: MorphingDialogProps) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return <MorphingDialogContext.Provider value={{ open, setOpen, id }}>{children}</MorphingDialogContext.Provider>;
}

function MorphingDialogTrigger({ children, className, id: elementId, onClick }: { children: React.ReactNode; className?: string; id?: string; onClick?: React.MouseEventHandler<HTMLDivElement> }) {
  const { setOpen, id } = useMorphingDialog();
  return <motion.div
    layoutId={`${id}-dialog`}
    id={elementId}
    role="button"
    tabIndex={0}
    className={cn("cursor-pointer", className)}
    onClick={(event) => { onClick?.(event); setOpen(true); }}
    onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") setOpen(true); }}
  >
    {children}
  </motion.div>;
}

function MorphingDialogContainer({ children }: { children: React.ReactNode }) {
  const { open, setOpen } = useMorphingDialog();
  if (typeof document === "undefined") return null;
  return createPortal(<AnimatePresence>{open && <motion.div
    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-md"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    onMouseDown={(event) => { if (event.target === event.currentTarget) setOpen(false); }}
  >{children}</motion.div>}</AnimatePresence>, document.body);
}

function MorphingDialogContent({ children, className, style }: { children: React.ReactNode; className?: string; style?: React.CSSProperties }) {
  const { id } = useMorphingDialog();
  return <motion.div layoutId={`${id}-dialog`} transition={{ type: "spring", bounce: 0.05, duration: 0.25 }} className={className} style={style}>{children}</motion.div>;
}

function MorphingDialogTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  const { id } = useMorphingDialog();
  return <motion.h2 layoutId={`${id}-title`} className={className}>{children}</motion.h2>;
}

function MorphingDialogSubtitle({ children, className }: { children: React.ReactNode; className?: string }) {
  const { id } = useMorphingDialog();
  return <motion.p layoutId={`${id}-subtitle`} className={className}>{children}</motion.p>;
}

function MorphingDialogImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const { id } = useMorphingDialog();
  return <motion.img layoutId={`${id}-image`} src={src} alt={alt} className={className} />;
}

function MorphingDialogDescription({ children, className, disableLayoutAnimation, variants }: { children: React.ReactNode; className?: string; disableLayoutAnimation?: boolean; variants?: Variants }) {
  return <motion.div layout={!disableLayoutAnimation} variants={variants} initial="initial" animate="animate" exit="exit" className={className}>{children}</motion.div>;
}

function MorphingDialogClose({ className }: { className?: string }) {
  const { setOpen } = useMorphingDialog();
  return <button type="button" aria-label="Close dialog" onClick={() => setOpen(false)} className={cn("absolute right-4 top-4 z-10 grid h-9 w-9 place-items-center rounded-full bg-slate-950/70 text-xl leading-none text-white transition hover:bg-slate-950", className)}>x</button>;
}

export { MorphingDialog, MorphingDialogTrigger, MorphingDialogContent, MorphingDialogTitle, MorphingDialogImage, MorphingDialogSubtitle, MorphingDialogClose, MorphingDialogDescription, MorphingDialogContainer };
