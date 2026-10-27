# Map art pass 1

Original code-drawn PixiJS art replaces the initial flat markers: layered conifers with shadows, faceted rock formations for hills, dune contours for desert, deterministic ground detail, a bunker and flag for neutral NPC garrisons, and a three-person infantry silhouette for world and tactical squads. Ground coordinates and selection geometry remain unchanged. Visual terrain height does not change combat rules.

Detail is seeded by absolute tile coordinates so refocusing a chunk does not randomize scenery. Unknown tiles receive no terrain decoration or garrison objects. Existing geometry memoization, reduced motion and march interpolation remain in place. No new textures or downloads are required. This is an incremental procedural art pass, not the final semi-realistic 3D-derived asset set. Real-device frame-rate validation remains outstanding.

Validation: TypeScript/Vite build and existing complete browser cycle, including mobile action placement, world march, tactical movement, capture, loot and reload. Screenshots exported by CI for visual review. No server changes or migrations.
