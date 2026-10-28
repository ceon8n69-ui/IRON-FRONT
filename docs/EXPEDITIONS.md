# Expeditions 0.2

## Playable sequence

Complete the first patrol, open Army → Units, form one army from a reserve squad, then choose an adjacent world hex. Move or capture costs 2 fuel and takes 30 server seconds. Neutral sites have no NPC garrison in this release. Return by adjacent movement to your own world base (see BASES.md; the shared staging tile 64:64 is legacy only).

The first slice deliberately has one army per player, one initial member and twelve controlled tiles. The normalized army_units relation allows capacity expansion later. The common staging tile is not an exclusive player base or claimable land. Individual world base placement, additional staging regions, PvP, guarded-site battles and army composition editing remain future work. A common staging tile limits expansion opportunities and is suitable for a small test cohort, not public-scale launch.

Captures must connect to the player's own base or existing territory. No other-player territory can be entered. Crossing neutral territory is allowed; it does not automatically establish control. A successful capture reveals surrounding terrain and grants minute production according to biome: plains 2 food, forest 2 metal, hills 3 metal, desert 2 oil. Current storage and offline limits apply. Production starts only after confirmed ownership; no retroactive gain while capture was pending.

If another player claims the target before this order is resolved, the order becomes blocked, the army remains at its source, and the travel fuel is spent. The first server transaction to resolve the claim wins. Territory ownership is protected by the tile row lock and a unique world/q/r primary key, not by client timestamps.

## Persistence and safety

- Player row locks serialize resource spending, army formation and commands.
- Idempotency keys bind to the full action payload; repeats return the original result.
- A partial unique index permits only one moving order per army.
- Ownership: lock existing hex row before checking/creating ownership; never acquire another player's lock.
- Worker, snapshot and world reads settle overdue orders using the same transaction logic. Reconnection loads the server snapshot.
- Each successful arrival stores explored cells. Current visibility is evaluated on the server. Explored-but-hidden cells reveal terrain only, not current ownership or enemy units.
- World reads request a bounded chunk (radius <= 8), not all 16,384 cells. Client polls the visible chunk every five seconds and stops when the map closes.
- New additive migration 9a3feb768692 creates armies, army_units, army_orders, tile_ownership and fog_of_war. No existing rows or tables are rewritten. The downgrade deletes expedition data and must never be run against production without separate approval and backup.

## Verification

Unit/integration coverage includes duplicate formation, request-key mismatch, fuel debit once, timer boundaries, connection-pool restart, no duplicate income, control cap, invalid coordinates, isolated claims, foreign army access, two-player concurrent capture, fog privacy and no-fuel rejection. Local PGlite run: 32 passed, two concurrency cases reserved for ordinary PostgreSQL in CI.

The Playwright sequence now continues beyond the original hero/build/train/PvE/equip/reload loop: forms an army, submits a capture, waits the real 30 seconds, reloads and checks ownership, army coordinates and fuel. The test exports a mobile world screenshot for visual review.
