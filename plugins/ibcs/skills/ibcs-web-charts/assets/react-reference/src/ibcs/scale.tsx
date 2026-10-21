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

/**
 * The clip of a pin tier (OURS): ±limit (default ±100 %), or tighter when one or a few pins are
 * outliers, i.e. more than `ratio` × the next-largest |Δ%| of the tier. The tier is then scaled from
 * the other pins: the outliers are drawn clipped at the tier edge with the outlier triangle and keep
 * their full label. One immaterial reference (AC 0 against a budget that rounds to 0, so −100 %)
 * must not flatten every other pin of the chart. ratio 0 turns the rule off.
 */
export function pinClip(values: Iterable<number | null | undefined>, limit = 1, ratio = 3): number {
  const a = [...values].filter((v): v is number => v != null && Number.isFinite(v) && v !== 0)
    .map((v) => Math.min(Math.abs(v), limit)).sort((x, y) => y - x);
  if (!(ratio > 0) || a.length < 2) return limit;
  // the outliers are the few pins above the deepest gap: a[j] > ratio × a[j + 1], at most half of the tier
  let first = -1;
  for (let j = 0; j + 1 < a.length && j + 1 <= a.length / 2; j++) if (a[j]! > ratio * a[j + 1]!) first = j + 1;
  // clip a little beyond the largest regular pin, so it stays the longest stem
  return first < 0 ? limit : Math.min(limit, a[first]! * 1.15);
}

/**
 * The scaling marker of a pin tier on its own scale (UN 5.2 / CH 4.3; OURS sizing): the round value
 * 1/2/5 × 10^n (as a fraction, 0.1 = 10 %) whose length is 25–60 % of the tier, so the reader can see
 * that this tier's % scale differs from the page's other % tiers.
 */
export function pinScaleBand(tierPx: number, ppu: number): number {
  const candidates = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1];
  const fit = candidates.find((c) => c * ppu >= 0.25 * tierPx && c * ppu <= 0.6 * tierPx);
  if (fit) return fit;
  const tooLong = candidates.filter((c) => c * ppu <= 0.6 * tierPx);
  return tooLong.length ? tooLong[tooLong.length - 1]! : candidates[0]!;
}

export type PinTier = { id: string; min: number; max: number; tierPx: number; /** charts read together share a group */ group?: string };
export type PinTierScale = { ppu: number; band: number | null; differs: boolean };

/**
 * Pin scales for every pin tier of a page (OURS): each tier (or group of charts read together, such
 * as the months and their Total) gets its own scale sized to its tier; when the scales differ across
 * the page, every tier gets a scaling marker of the same round value within a group.
 */
export function pagePinScales(tiers: PinTier[], fill = 0.9): Map<string, PinTierScale> {
  const groups = new Map<string, PinTier[]>();
  for (const t of tiers) groups.set(t.group ?? t.id, [...(groups.get(t.group ?? t.id) ?? []), t]);
  const ppuOf = new Map<string, number>();
  for (const [g, ts] of groups) ppuOf.set(g, pinScale(ts, fill));
  const values = [...ppuOf.values()];
  const differs = values.some((v) => Math.abs(v - values[0]!) > 0.01 * Math.max(v, values[0]!));
  const out = new Map<string, PinTierScale>();
  for (const [g, ts] of groups) {
    const ppu = ppuOf.get(g)!;
    const band = differs ? pinScaleBand(Math.min(...ts.map((t) => t.tierPx)), ppu) : null;
    for (const t of ts) out.set(t.id, { ppu, band, differs });
  }
  return out;
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
