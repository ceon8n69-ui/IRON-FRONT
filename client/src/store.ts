import { create } from "zustand";
export type Building = {
  id: string;
  kind: string;
  q: number;
  r: number;
  level: number;
  status: string;
  ready_at: number;
  upgrade_ready_at?: number | null;
  max_level?: number;
  upgrade?: { cost: Record<string, number>; seconds: number } | null;
  effects?: { current: Effects; next: Effects | null };
};
export type Effects = { output: Record<string, number>; input: Record<string, number>; power: number; storage: number; vision: number; repair: number };
export type Stack = { id:string; side:"player"|"npc"; kind:string; count:number; start:number; hp:number; pos:number[]; acted:boolean; defending:boolean; unit_id?:string; each?:number; art?:string; trait?:string|null; faction?:string|null };
export type Preview = { reach:boolean; damage:number[]; kills:number[]; retaliation:{damage:number[];kills:number[]}|null };
export type Battle = {
  id: string;
  status: string;
  balance_version: string;
  preview?: Record<string, Preview>;
  state: {
    loot?: {item_id:string;definition_id:string;table_version:string};
    captured?: boolean;
    expedition?: {army_id:string;order_id:string;q:number;r:number};
    pvp?: {target:"base"|"territory"|"mine";defender_id:string;defender:string;result?:string;loot?:Record<string,number>};
    turn: number;
    round?: number;
    stacks?: Stack[];
    order?: string[];
    active?: string | null;
    ability_used?: boolean;
    led?: boolean;
    npc_tier?: {name:string;hp:number;xp:number};
    cover: number[][];
    terrain?: string;
  };
};
export type State = {
  player: { id: string; name: string };
  revision: number;
  server_time: number;
  resources: Record<string, number>;
  buildings: Building[];
  jobs: { id: string; ready_at: number }[];
  units: { id: string; kind: string; count: number; hp: number; status: string }[];
  hero: { kind: string; xp: number } | null;
  inventory: { id: string; definition_id: string; equipped: boolean; source:string; definition:{name:string;rarity:string;damage_bonus:number;image:string;slot?:string;slot_name?:string;perks?:Record<string,number>} }[];
  commander?: CommanderView | null;
  battles: Battle[];
  first_victory: boolean;
  base: {q:number;r:number} | null;
  storage_cap?: number;
  mines?: {q:number;r:number;resource:string;rate:number}[];
  pending_chests?: {q:number;r:number;options:{resources:Record<string,number>;xp:number}}[];
  armies: Army[];
  armies_max?: number;
  territories: Territory[];
  pvp?: PvpState;
  doctrines?: { branches: Record<string,string>; doctrines: DoctrineView[]; effects: Record<string,number> };
  vp?: number;
  raids?: { q:number; r:number; target_q:number; target_r:number; strikes_at:number; status:string; result:string|null }[];
  alliance?: AllianceView | null;
  calendar?: Calendar | null;
  upkeep?: Record<string, number>;
  control_limit?: number;
  nodes?: {q:number;r:number;kind:string;name:string;supplied:boolean}[];
};
export type DoctrineView = { key:string; branch:string; tier:number; name:string; about:string; cost:Record<string,number>; seconds:number; state:"available"|"research"|"done"; ready_at:number|null };
export type AllianceView = { id:string; name:string; tag:string; code:string; owner:boolean; max:number; vp:number; members:{id:string;name:string;vp:number;hero:string|null;owner:boolean;me:boolean}[] };
export type Calendar = { season:number; day:number; week:number; day_index:number; day_started_at:number; next_day_at:number; ends_at:number; event:{key:string;name:string;about:string} };
export type SkillView = { key:string; name:string; icon:string; rank:number; about:string };
export type CommanderView = { level:number; xp:number; level_xp:number; next_xp:number|null; pending:number; offers:SkillView[]; skills:SkillView[]; perks:Record<string,number>; max_skills:number };
export type PvpReport = { id:string; role:"attacker"|"defender"; enemy:string; target:"base"|"territory"|"mine"; q:number; r:number; outcome:"victory"|"defeat"; loot:Record<string,number>; losses:{attacker?:Record<string,number>;defender?:Record<string,number>}; created_at:number };
export type PvpState = { shield_until:number; newbie:boolean; incoming:{q:number;r:number;target:string;attacker:string;arrive_at:number}[]; reports:PvpReport[] };
export type TargetPreview = { kind:"base"|"territory"|"mine"; title:string; defender:string; hero:string|null; shield_until:number; allowed:boolean; reason:string|null; forces:{kind:string;name:string;count:number;approx:boolean;militia:boolean}[]; my_shield_until:number; loses_shield:boolean; attacks_left:number };
type Store = {
  state: State | null;
  token: string;
  connected: boolean;
  setState: (s: State) => void;
  setToken: (t: string) => void;
  setConnected: (v: boolean) => void;
};
export const useGame = create<Store>((set) => ({
  state: null,
  token: sessionStorage.getItem("iron-session") || "",
  connected: false,
  setState: (state) =>
    set((s) =>
      !s.state || state.revision >= s.state.revision ? { state } : {},
    ),
  setToken: (token) => {
    sessionStorage.setItem("iron-session", token);
    set({ token });
  },
  setConnected: (connected) => set({ connected }),
}));
export async function request(path: string, body?: unknown, key?: string) {
  const token = useGame.getState().token;
  const r = await fetch("/api/v1" + path, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: "Bearer " + token } : {}),
      ...(key ? { "Idempotency-Key": key } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok)
    throw new Error(
      typeof data.detail === "string" ? data.detail : "Ошибка запроса",
    );
  return data;
}
export async function command(path: string, body: unknown) {
  const key = crypto.randomUUID();
  // A network retry uses the same idempotency key, including after uncertain response loss.
  let data;
  try {
    data = await request(path, body, key);
  } catch (e) {
    if (e instanceof TypeError) data = await request(path, body, key);
    else throw e;
  }
  useGame.getState().setState(data.state);
  return data;
}

export type MarchOrder = { id:string; q:number; r:number; from_q:number; from_r:number; action:string; status:string; started_at:number; ready_at:number; finished_at:number|null; result:string|null; path?: number[][] | null };
export type Army = { id:string; number:number; commander:boolean; in_battle?:boolean; q:number; r:number; status:string; unit_ids:string[]; orders:MarchOrder[]; movement:number; movement_max:number; movement_next_at:number|null };
export type RoutePreview = { path:number[][]; cost:number; fuel:number; seconds:number; movement:number; affordable:boolean };
export type MapObject = { kind:"pile"|"chest"|"mine"|"ruin"|"camp"; resource?:string; amount?:number; rate?:number; owner?:"self"|"other"|null; pending?:boolean; unit?:string; name?:string; count?:number; cost?:Record<string,number>; available?:boolean; faction?:string|null };
export type WorldTile = { q:number; r:number; biome:string; visibility:string; control:"self"|"other"|"ally"|"neutral"|null; home:boolean; base?:"self"|"other"|"ally"|"staging"|null; garrison?:boolean; garrison_strength?:{name:string;hp:number;xp:number}|null; object?:MapObject|null; node?:{kind:string;name:string;about:string;yield:Record<string,number>;vision:number}|null; supplied?:boolean|null };
export type Territory = { q:number; r:number; biome:string; yield:Record<string,number>; acquired_at:number; supplied?:boolean; node?:string|null };
export type ExpeditionRules = {staging:number[];movement_max:number;movement_regen_seconds:number;terrain_cost:Record<string,number>;step_seconds:number;seconds:number;fuel:number;control_limit:number;army_vision:number;territory_yield:Record<string,Record<string,number>>};
