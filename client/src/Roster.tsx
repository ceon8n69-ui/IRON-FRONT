/*
 * Unit-row preview from pre-rendered sprites (public/art/units/<key>.png, made by
 * tools/render-units.mjs). Plain images: no WebGL context per preview.
 */
export function Roster({ units, height = 92 }: { units: { art: string; key: string }[]; faction?: string; height?: number; scale?: number }) {
  return <div className="roster" style={{ height }} aria-hidden="true">
    {units.map((u) => <img key={u.key} src={`/art/units/${u.key}.png`} alt="" loading="lazy" decoding="async" />)}
  </div>;
}
