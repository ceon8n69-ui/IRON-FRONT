const paths:Record<string,string>={
 base:'M3 11 12 3l9 8M5 10v11h14V10M9 21v-7h6v7',
 army:'M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6l-8-3ZM8 11h8M12 7v8',
 map:'M2 6l6-3 8 3 6-3v15l-6 3-8-3-6 3V6ZM8 3v15M16 6v15',
 alliance:'M5 21V3m0 1h14l-3 4 3 4H5',
 command:'M4 5h16M4 12h16M4 19h16M8 3v4M16 10v4M10 17v4',
 target:'M12 2v4M12 18v4M2 12h4M18 12h4M19 12a7 7 0 1 1-14 0 7 7 0 1 1 14 0M12 10v4M10 12h4',
};
export function Icon({name}:{name:string}){return <svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]||paths.target}/></svg>}
