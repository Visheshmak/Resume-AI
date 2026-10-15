import {
  ImageComparison,
  ImageComparisonImage,
  ImageComparisonSlider,
} from "./ui/image-comparison";

export function ImageComparisonSpring() {
  return <ImageComparison
    className="aspect-16/10 w-full rounded-3xl border border-slate-700/70"
    enableHover
    springOptions={{ bounce: 0.3 }}
  >
    <ImageComparisonImage src="/resume-dark.svg" alt="Resume report before optimization" position="left" />
    <ImageComparisonImage src="/resume-light.svg" alt="Resume report after optimization" position="right" />
    <ImageComparisonSlider className="w-0.5 bg-white/40 backdrop-blur-sm" />
  </ImageComparison>;
}
