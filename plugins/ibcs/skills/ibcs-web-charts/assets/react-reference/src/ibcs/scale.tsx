// One px per unit per scale group on a page (behaviour contract §5). The registry hands out px
// per unit, never a domain: each chart sizes its own plot from its own range.
import { createContext, useContext, useId, useLayoutEffect, useMemo, useState, type ReactNode } from "react";

export type ScaleRequest = {
  /** Scale group key: "EUR", "t", "%" (pins and pp share "%"), or "EUR:total" for an own scale. */
  unit: string;
  min: number;
  max: number;
  /** The most plot px the chart may use for this extent, after its own label rooms and gaps. */
  availablePx: number;
};

/** Smallest px per unit per group; zero is always inside the span; non-positive requests are skipped. */
export function pxPerUnit(requests: Iterable<ScaleRequest>): Map<string, number> {
  const out = new Map<string, number>();
  for (const r of requests) {
    const span = Math.max(r.max, 0) - Math.min(r.min, 0);
    if (!(span > 0) || !(r.availablePx > 0)) continue;
    const ppu = r.availablePx / span;
    out.set(r.unit, Math.min(out.get(r.unit) ?? Infinity, ppu));
  }
  return out;
}

type Registry = {
  ppu: Map<string, number>;
  register: (id: string, requests: ScaleRequest[]) => void;
  unregister: (id: string) => void;
};

const ScaleContext = createContext<Registry | null>(null);

/**
 * Page scale registry. `fixed` sets px per unit exactly for server rendering and print
 * (e.g. { EUR: 40 / 1e6 }); a fixed group ignores the charts' requests.
 */
export function ScaleProvider({ children, fixed }: { children: ReactNode; fixed?: Record<string, number> }) {
  const [requests, setRequests] = useState<Record<string, ScaleRequest[]>>({});
  const value = useMemo<Registry>(() => {
    const ppu = pxPerUnit(Object.values(requests).flat());
    for (const [unit, v] of Object.entries(fixed ?? {})) ppu.set(unit, v);
    return {
      ppu,
      register: (id, reqs) =>
        setRequests((prev) => (JSON.stringify(prev[id]) === JSON.stringify(reqs) ? prev : { ...prev, [id]: reqs })),
      unregister: (id) =>
        setRequests((prev) => {
          const { [id]: _drop, ...rest } = prev;
          return rest;
        }),
    };
  }, [requests, fixed]);
  return <ScaleContext.Provider value={value}>{children}</ScaleContext.Provider>;
}

/**
 * Register this chart's extents and read back the page's px per unit for each requested group.
 * Returns undefined for a group until the first layout pass has run (render nothing until then).
 */
export function useScale(requests: ScaleRequest[]): Map<string, number | undefined> {
  const registry = useContext(ScaleContext);
  const id = useId();
  const key = JSON.stringify(requests);
  useLayoutEffect(() => {
    registry?.register(id, requests);
    return () => registry?.unregister(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [registry, id, key]);
  const own = registry ? null : pxPerUnit(requests);
  return new Map(requests.map((r) => [r.unit, (registry?.ppu ?? own)!.get(r.unit)]));
}
