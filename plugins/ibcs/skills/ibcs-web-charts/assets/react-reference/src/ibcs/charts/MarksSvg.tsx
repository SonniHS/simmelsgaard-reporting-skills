// Thin renderer: marks → <svg>. No logic beyond mapping; hatch patterns live in this SVG's own
// <defs> with ids unique per instance (url(#…) breaks across iframes and shadow roots).
import { useId, type CSSProperties } from "react";
import { tokens } from "../tokens.generated";
import type { Fill, Layout, Mark } from "./marks";

export type MarksSvgProps = {
  layout: Layout;
  /** The IBCS title lines as one accessible name. */
  title: string;
  desc?: string;
  /** Category zones become focusable buttons. */
  onSelect?: (category: string) => void;
  /** Only the <svg>, with xmlns, for previews and server rendering (no hidden table). */
  standalone?: boolean;
};

const hidden: CSSProperties = { position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)", whiteSpace: "nowrap" };
const P = tokens.pattern.fcHatch;

export function MarksSvg({ layout, title, desc, onSelect, standalone }: MarksSvgProps) {
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const stripes = [...new Set(layout.marks.flatMap((m) => ("fill" in m && m.fill && typeof m.fill === "object" ? [m.fill.hatch] : [])))];
  const patternId = (stripe: string) => `${id}-hatch-${stripes.indexOf(stripe)}`;
  const paint = (f: Fill | undefined) => (f == null ? "none" : typeof f === "string" ? f : `url(#${patternId(f.hatch)})`);
  const data = (m: Mark) => ({ "data-role": m.role, "data-impact": m.impact, "data-category": m.category });

  const svg = (
    <svg
      xmlns={standalone ? "http://www.w3.org/2000/svg" : undefined}
      role="img"
      aria-labelledby={`${id}-t${desc ? ` ${id}-d` : ""}`}
      width={layout.width}
      height={layout.height}
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ display: "block", background: tokens.color.background.page, fontFamily: tokens.typography.family.web.join(", "), fontVariantNumeric: "tabular-nums" }}
    >
      <title id={`${id}-t`}>{title}</title>
      {desc && <desc id={`${id}-d`}>{desc}</desc>}
      <defs>
        {stripes.map((s) => (
          <pattern key={s} id={patternId(s)} patternUnits="userSpaceOnUse" width={P.periodPx} height={P.periodPx} patternTransform={`rotate(${P.angleDeg})`}>
            <rect width={P.periodPx} height={P.periodPx} fill={tokens.color.scenario.fc.ground} />
            <rect width={P.periodPx * P.stripeShare} height={P.periodPx} fill={s} />
          </pattern>
        ))}
      </defs>
      {layout.marks.map((m, i) => {
        switch (m.kind) {
          case "rect":
            if (m.role === "hit") {
              if (!onSelect || !m.category) return null;
              const c = m.category;
              return (
                <rect key={i} {...data(m)} x={m.x} y={m.y} width={m.w} height={m.h} fill="transparent" role="button" tabIndex={0} aria-label={m.tooltip ?? c}
                  onClick={() => onSelect(c)}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(c); } }}>
                  <title>{m.tooltip ?? c}</title>
                </rect>
              );
            }
            return <rect key={i} {...data(m)} x={m.x} y={m.y} width={Math.max(0, m.w)} height={Math.max(0, m.h)} fill={paint(m.fill)} stroke={m.stroke} strokeWidth={m.strokeWidth} shapeRendering="crispEdges" />;
          case "line":
            return <line key={i} {...data(m)} x1={m.x1} y1={m.y1} x2={m.x2} y2={m.y2} stroke={m.stroke} strokeWidth={m.strokeWidth} />;
          case "path":
            return <path key={i} {...data(m)} d={m.d} fill={paint(m.fill)} stroke={m.stroke} strokeWidth={m.strokeWidth} />;
          case "ellipse":
            return <ellipse key={i} {...data(m)} cx={m.cx} cy={m.cy} rx={m.rx} ry={m.ry} fill="none" stroke={m.stroke} strokeWidth={m.strokeWidth} />;
          case "text":
            return (
              <text key={i} {...data(m)} x={m.x} y={m.y} textAnchor={m.anchor} dominantBaseline="central" fontSize={m.size} fontWeight={m.weight} fill={m.fill}>
                {m.text}
              </text>
            );
        }
      })}
    </svg>
  );
  if (standalone) return svg;
  const [head, ...body] = layout.table;
  return (
    <figure style={{ margin: 0, position: "relative", maxWidth: "100%" }}>
      {svg}
      <div style={hidden}>
        <table>
          <caption>{title}</caption>
          <thead><tr>{head?.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
          <tbody>{body.map((r, i) => <tr key={i}>{r.map((c, k) => (k === 0 ? <th key={k} scope="row">{c}</th> : <td key={k}>{c}</td>))}</tr>)}</tbody>
        </table>
      </div>
    </figure>
  );
}
