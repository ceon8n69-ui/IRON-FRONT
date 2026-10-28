# World bases · 0.3

## What changed

Every commander now has one exclusive base hex on the 128×128 world map instead of the shared staging tile 64:64. The base is the player's home point for vision, army formation, territory linking and the tutorial garrison.

## Placement rules

- Sites come from a fixed grid with step 10 and a 6-hex edge margin, ordered by distance from the map centre. The world fits 141 bases.
- Hex distance between any two bases is at least 10, so safe zones never overlap.
- A site is skipped when another player's territory is within 5 hexes or any army is within 3 hexes.
- The legacy staging point 64:64 and everything within 10 hexes of it are never assigned.
- New players get a base at registration. Players who existed before this release get one lazily on their next authenticated request.
- Assignment takes the player's row lock plus a transaction advisory lock `(1717, 1)`. The unique `(world_id, q, r)` constraint is the database backstop. Eight simultaneous first logins are covered by a test.
- When no site is free, registration returns 503 with a clear message. No player is created half-way.

## Gameplay rules

- A new army forms on the player's own base.
- Vision radius 3 (Valkyrie 4) is counted from the base.
- A capture must touch the player's base or an existing territory.
- Every base has a tutorial NPC garrison directly south of it, at (q, r+1). The rest of the safe zone (|dq|+|dr| ≤ 4) has no garrisons. The first eastward hex is always open.
- A base is never claimable territory. Another player's base can only be raided with an explicit attack order (see PVP.md); it is never captured.
- The world endpoint marks visible bases as `self`, `other` or `staging`. Hidden foreign bases are not disclosed.
- The snapshot exposes `base: {q, r}`. The client centres the map on it and shows "Моя база" and the sector number.

## Legacy data

Migration `b7c41e2d9f05` only creates `player_bases` and rewrites no existing rows. Territories captured around 64:64 before this release stay owned and keep producing. The army stays where it was and can walk anywhere step by step. New captures there need a link to an existing territory, because 64:64 is no longer a player's home. Balance version is now `slice-3`, because the garrison layout depends on bases.

## Verification

- 50 Python tests pass on local PostgreSQL 16, including 9 new ones in `test_bases.py`: grid spacing, garrison rule, distinct and persistent bases, concurrent logins, lazy assignment, avoiding holdings, full world, base markers and fog, foreign base rejection mid-march.
- Expedition and garrison tests now use coordinates relative to the player's base.
- Alembic upgrade, seed and check pass.
- The Playwright mobile cycle passes with real timers on Chromium. It now checks that capture and garrison victory happen next to the player's own base.

## Not done yet

Base relocation, more than one world, and widening the grid when 141 sites fill up.
