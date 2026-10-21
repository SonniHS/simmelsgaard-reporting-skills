// One px per unit per scale group on a page (behaviour contract §5). The registry hands out px
// per unit, never a domain: each chart sizes its own plot from its own range.
import { createContext, useCallback, useContext, useId, useLayoutEffect, useMemo, useState, type ReactNode } from "react";

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

/**
 * px per 1.0 (= 100 %) for every pin tier of a page (the "%" group): each tier's largest clipped
 * |Δ%| may fill 90 % of its extent (OURS defaults: 48 px column tiers, 90 px bar tiers); the
 * smallest wins, so pins stay comparable across the page and the largest one fills its tier.
 */
export function pinScale(tiers: Iterable<{ min: number; max: number; tierPx: number }>, fill = 0.9): number {
  let ppu = Infinity;
  for (const t of tiers) {
    const reach = Math.max(Math.abs(t.min), Math.abs(t.max));
    if (reach > 0 && t.tierPx > 0) ppu = Math.min(ppu, (fill * t.tierPx) / reach);
  }
  return Number.isFinite(ppu) ? ppu : 100;
}

type Api = {
  register: (id: string, requests: ScaleRequest[]) => void;
  unregister: (id: string) => void;
};

// Two contexts: a stable API (never changes, so registering charts never re-run their effects) and
// the current px per unit (changes when a request changes). One context for both made every
// registration re-run every chart's effect: "Maximum update depth exceeded" with two charts.
const ApiContext = createContext<Api | null>(null);
const PpuContext = createContext<Map<string, number> | null>(null);

/**
 * Page scale registry. `fixed` sets px per unit exactly for server rendering and print
 * (e.g. { EUR: 40 / 1e6 }); a fixed group ignores the charts' requests.
 */
export function ScaleProvider({ children, fixed }: { children: ReactNode; fixed?: Record<string, number> }) {
  const [requests, setRequests] = useState<Record<string, string>>({});
  const register = useCallback((id: string, reqs: ScaleRequest[]) => {
    const json = JSON.stringify(reqs);
    setRequests((prev) => (prev[id] === json ? prev : { ...prev, [id]: json }));
  }, []);
  const unregister = useCallback((id: string) => {
    setRequests((prev) => {
      if (!(id in prev)) return prev;
      const { [id]: _drop, ...rest } = prev;
      return rest;
    });
  }, []);
  const api = useMemo<Api>(() => ({ register, unregister }), [register, unregister]);
  const fixedKey = JSON.stringify(fixed ?? {});
  const ppu = useMemo(() => {
    const map = pxPerUnit(Object.values(requests).flatMap((j) => JSON.parse(j) as ScaleRequest[]));
    for (const [unit, v] of Object.entries(JSON.parse(fixedKey) as Record<string, number>)) map.set(unit, v);
    return map;
  }, [requests, fixedKey]);
  return (
    <ApiContext.Provider value={api}>
      <PpuContext.Provider value={ppu}>{children}</PpuContext.Provider>
    </ApiContext.Provider>
  );
}

/**
 * Register this chart's extents and read back the page's px per unit for each requested group.
 * Returns undefined for a group until the first layout pass has run (render nothing until then).
 * The effect depends only on the stable API, the chart's id and the requests' JSON.
 */
export function useScale(requests: ScaleRequest[]): Map<string, number | undefined> {
  const api = useContext(ApiContext);
  const ppu = useContext(PpuContext);
  const id = useId();
  const key = JSON.stringify(requests);
  useLayoutEffect(() => {
    if (!api) return;
    api.register(id, JSON.parse(key) as ScaleRequest[]);
    return () => api.unregister(id);
  }, [api, id, key]);
  const map = ppu ?? pxPerUnit(requests);
  return new Map(requests.map((r) => [r.unit, map.get(r.unit)]));
}
