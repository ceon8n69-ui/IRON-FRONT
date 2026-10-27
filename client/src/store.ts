import { create } from "zustand";
export type Building = {
  id: string;
  kind: string;
  q: number;
  r: number;
  level: number;
  status: string;
  ready_at: number;
};
export type Battle = {
  id: string;
  status: string;
  balance_version: string;
  state: {
    expedition?: {army_id:string;order_id:string;q:number;r:number};
    turn: number;
    player: { pos: number[]; hp: number };
    npc: { pos: number[]; hp: number };
    cover: number[][];
  };
};
export type State = {
  player: { id: string; name: string };
  revision: number;
  server_time: number;
  resources: Record<string, number>;
  buildings: Building[];
  jobs: { id: string; ready_at: number }[];
  units: { id: string; hp: number; status: string }[];
  hero: { kind: string; xp: number } | null;
  inventory: { id: string; definition_id: string; equipped: boolean }[];
  battles: Battle[];
  first_victory: boolean;
  armies: Army[];
  territories: Territory[];
};
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

export type MarchOrder = { id:string; q:number; r:number; from_q:number; from_r:number; action:string; status:string; started_at:number; ready_at:number; finished_at:number|null; result:string|null };
export type Army = { id:string; q:number; r:number; status:string; unit_ids:string[]; orders:MarchOrder[] };
export type WorldTile = { q:number; r:number; biome:string; visibility:string; control:"self"|"other"|"neutral"|null; home:boolean; garrison?:boolean };
export type Territory = { q:number; r:number; biome:string; yield:Record<string,number>; acquired_at:number };
export type ExpeditionRules = {home:number[];seconds:number;fuel:number;control_limit:number;army_vision:number;territory_yield:Record<string,Record<string,number>>};
