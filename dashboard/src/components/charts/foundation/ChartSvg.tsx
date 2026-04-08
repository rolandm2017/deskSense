import { PropsWithChildren } from "react";

interface ChartSvgProps extends PropsWithChildren {
  viewBoxWidth: number;
  viewBoxHeight: number;
  className?: string;
}

function ChartSvg({
  viewBoxWidth,
  viewBoxHeight,
  className,
  children,
}: ChartSvgProps) {
  return (
    <svg
      className={className}
      viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
      preserveAspectRatio="none"
    >
      {children}
    </svg>
  );
}

export default ChartSvg;
