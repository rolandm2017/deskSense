export interface ChartPoint {
  x: number;
  y: number;
}

export function scaleLinear(value: number, domainMin: number, domainMax: number, rangeMin: number, rangeMax: number) {
  if (domainMax === domainMin) {
    return rangeMin;
  }

  const pct = (value - domainMin) / (domainMax - domainMin);
  return rangeMin + pct * (rangeMax - rangeMin);
}

export function buildPolylinePath(points: ChartPoint[]): string {
  return points.map((point) => `${point.x},${point.y}`).join(" ");
}

export function buildAreaPath(points: ChartPoint[], floorY: number): string {
  if (points.length === 0) {
    return "";
  }

  return `${points[0].x},${floorY} ${buildPolylinePath(points)} ${points[points.length - 1].x},${floorY}`;
}
