# Garrison equipment drops v1

Each newly won and successfully captured NPC garrison grants exactly one unique tactical module, in the same player/tile-locked transaction as ownership and 50 XP. Defeat or a victory after another player has claimed the tile grants no item. Earlier completed victories are not reprocessed.

Version gar-loot-v1 deterministically derives the roll from the battle seed: 0–69 uncommon Trophy Module (+3% damage), 70–94 rare Precision Module (+4%), 95–99 epic Vanguard Module (+5%). The battle stores the roll, table version, item ID and definition ID. Item.source_id has a database unique constraint. Ownership history records issuance. No reroll or client-supplied stats are accepted.

Only one module can be equipped. The server resolves its definition and caps equipment damage bonus at 5%; effects do not stack. Changing equipment during combat remains forbidden. Existing tutorial module keeps its +3%. Versioned definitions are code configuration; no schema migration is needed.

The inventory displays server-provided names, rarity, bonus and origin. Three variants currently share the original module illustration with different rarity frames. This is not a full equipment catalog: more slots, distinct illustrations, upgrades, sets, trading and Stars are not implemented in this step. Drops are not blockchain NFTs.
