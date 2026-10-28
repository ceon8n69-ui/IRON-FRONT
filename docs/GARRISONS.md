# World garrisons

Neutral garrisons use the existing deterministic 9×9 combat engine. Each base has its tutorial target directly south (q, r+1); more targets use a fixed server coordinate rule outside every base safe zone (see BASES.md). Previously owned tiles remain owned and do not gain a garrison. Hidden targets are not disclosed by the world endpoint.

A 30-second march costing 2 fuel starts the battle on arrival. The army stays at its source until victory. New orders and equipment changes are blocked during combat. Battle state includes the originating army, order and target, persisted in the existing battles JSON state; no migration is needed. Reload resumes the same fight.

Victory claims the tile under its PostgreSQL row lock and awards 50 commander XP once. If two players attack the same neutral garrison, both may fight, but only the first eligible victorious transaction acquires ownership and XP. No extra equipment or repeatable resource reward is added in this step. Defeat restores at least 50 squad HP at the source tile. Existing tutorial rewards remain separate.

The world marker and action panel show NPC status. Tactical commands for expedition battles remain above navigation in a viewport-bound scene. Tests cover victory, defeat, reload, ownership checks, repeated final commands and competing victories. Browser coverage extends the original complete cycle with a real march, reload during battle and territory capture.

Limitations: one squad, one garrison strength (55 HP), no garrison respawn, no retreat button or battle expiration yet (defeat after 50 rounds), no equipment drop tables.
