import { Graphics } from 'pixi.js';

// Original procedural art. Coordinates seed stable detail across chunk changes.
export function noise(q:number,r:number,i:number) {
 let n=Math.imul(q+113,374761393)^Math.imul(r+71,668265263)^Math.imul(i+1,1274126177);
 n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967296;
}
const INK = 0x1b201e;
const ink = { color: INK, width: 1.4, alignment: 0.5 } as const;
export function surface(x:number,y:number,biome:string,q:number,r:number) {
 const g=new Graphics();if(biome==='unknown')return g;
 const dry=biome==='desert'||biome==='beach';
 if(biome==='sea'||biome==='lake'){
  // Wave crests, seeded so they stay put when the chunk refocuses.
  for(let i=0;i<5;i++){const px=x+(noise(q,r,i*5)-.5)*60,py=y+(noise(q,r,i*5+1)-.5)*28;
   g.moveTo(px-6,py).quadraticCurveTo(px-3,py-3,px,py).quadraticCurveTo(px+3,py-3,px+6,py).stroke({color:0xd6efff,width:1.4,alpha:.7});}
  return g;
 }
 if(biome==='river'){
  g.moveTo(x-44,y+2).bezierCurveTo(x-18,y-14,x+12,y+14,x+44,y-4).stroke({color:0x2f6fa8,width:16,alpha:.55});
  g.moveTo(x-44,y+2).bezierCurveTo(x-18,y-14,x+12,y+14,x+44,y-4).stroke({color:0x7cc1ea,width:9});
  g.moveTo(x-20,y-3).lineTo(x-12,y-5).moveTo(x+10,y+4).lineTo(x+18,y+2).stroke({color:0xe6f6ff,width:1.2});
  return g;
 }
 // Grass tufts, pebbles and the odd flower, seeded by world coordinates.
 for(let i=0;i<16;i++){
  const px=x+(noise(q,r,i*3)-.5)*70,py=y+(noise(q,r,i*3+1)-.5)*34,n=noise(q,r,i*3+2);
  if(dry){ g.ellipse(px,py,2+n*3,1).fill({color:0xb9934f,alpha:.45}); continue; }
  if(n<.55) g.moveTo(px-2,py).lineTo(px-1,py-4).moveTo(px,py).lineTo(px+1,py-5).moveTo(px+2,py).lineTo(px+3,py-3).stroke({color:0x3f7a30,width:1.4});
  else if(n<.75) g.ellipse(px,py,2.4,1.4).fill(0x9aa092).stroke({color:INK,width:.8});
  else if(biome==='plain') g.circle(px,py-1,1.6).fill([0xf2e9a5,0xa9b7f0,0xf3b0c6][i%3]);
 }
 return g;
}
function rock(g:Graphics,x:number,y:number,w:number,h:number){
 g.ellipse(x+3,y+3,w,w*.35).fill({color:0x0b181c,alpha:.28});
 g.poly([x-w,y,x-w*.6,y-h*.75,x+w*.1,y-h,x+w*.8,y-h*.55,x+w,y,x+w*.2,y+w*.3]).fill(0x8d948a).stroke(ink);
 g.poly([x+w*.1,y-h,x+w*.8,y-h*.55,x+w,y,x+w*.2,y+w*.3,x,y-h*.4]).fill(0x6b7268);
 g.poly([x-w*.6,y-h*.75,x+w*.1,y-h,x,y-h*.4]).fill(0xb4b8ab);
 g.ellipse(x-w*.4,y-2,w*.35,2.2).fill(0x5a9a3c);
}
function roundTree(g:Graphics,x:number,y:number,h:number,tone:number){
 const leaf=[0x4f9a3a,0x3e8a3f,0x7fb247,0xd8a23a][tone%4];
 const dark=[0x3b7a2e,0x2f6c33,0x5f9236,0xb07b26][tone%4];
 g.ellipse(x+5,y+2,h*.45,h*.16).fill({color:0x0b181c,alpha:.28});
 g.roundRect(x-2.5,y-h*.45,5,h*.45,1.5).fill(0x7a5434).stroke(ink);
 for(const [dx,dy,rr] of [[-h*.2,-h*.62,h*.27],[h*.2,-h*.62,h*.27],[0,-h*.82,h*.3],[0,-h*.55,h*.3]] as const)
  g.circle(x+dx,y+dy,rr).fill(leaf).stroke(ink);
 g.circle(x+h*.12,y-h*.62,h*.2).fill(dark);
 g.circle(x-h*.08,y-h*.9,h*.1).fill({color:0xffffff,alpha:.18});
}
function pine(g:Graphics,x:number,y:number,h:number){
 g.ellipse(x+5,y+2,h*.32,h*.12).fill({color:0x0b181c,alpha:.28});
 g.rect(x-2,y-h*.2,4,h*.2).fill(0x6e4b2f).stroke(ink);
 for(let k=0;k<3;k++){
  const by=y-h*.15-k*h*.24,w=h*(.34-k*.08),top=by-h*.36;
  g.poly([x,top,x-w,by,x+w,by]).fill(k===2?0x5d9a43:0x3f7f3b).stroke(ink);
  g.poly([x,top,x,by,x+w,by]).fill(0x2f6633);
 }
}
function bush(g:Graphics,x:number,y:number,flower:number|null){
 g.ellipse(x+2,y+1,9,3).fill({color:0x0b181c,alpha:.25});
 g.circle(x-4,y-4,5).fill(0x4f9a3a).stroke(ink);g.circle(x+4,y-4,5).fill(0x4f9a3a).stroke(ink);g.circle(x,y-7,5.5).fill(0x5fab45).stroke(ink);
 if(flower!==null) for(const [dx,dy] of [[-4,-6],[3,-8],[1,-3]]) g.circle(x+dx,y+dy,1.4).fill(flower);
}
function stump(g:Graphics,x:number,y:number){
 g.roundRect(x-5,y-6,10,7,2).fill(0x7a5434).stroke(ink);g.ellipse(x,y-6,5,2).fill(0xc49a64).stroke({color:INK,width:1});
}
function mushroom(g:Graphics,x:number,y:number){
 g.rect(x-.8,y-3,1.6,3).fill(0xeadfc8);g.ellipse(x,y-3.5,3,2).fill(0xd2453a).stroke({color:INK,width:.8});
}
export function environment(x:number,y:number,biome:string,q:number,r:number){
 const g=new Graphics();
 const n=(i:number)=>noise(q,r,i);
 if(biome==='forest'){
  const items=Array.from({length:5},(_,i)=>({tx:x+(n(i*2)-.5)*62,ty:y-14+i*6+(n(i*2+7)-.5)*6,h:26+n(i*2+1)*14,i}));
  items.sort((a,b)=>a.ty-b.ty);
  for(const t of items) (n(t.i+40)<.5?pine(g,t.tx,t.ty,t.h+6):roundTree(g,t.tx,t.ty,t.h,Math.floor(n(t.i+50)*5)));
  if(n(60)<.5) mushroom(g,x+(n(61)-.5)*40,y+12);
 } else if(biome==='hills'){
  rock(g,x-18,y-2,15,18);rock(g,x+10,y-4,21,30);rock(g,x+24,y+10,9,10);
  if(n(70)<.6) bush(g,x-26,y+12,null);
 } else if(biome==='mountain'){
  const peak=(px:number,py:number,w:number,h:number)=>{
   g.ellipse(px+4,py+3,w,w*.3).fill({color:0x0b181c,alpha:.28});
   g.poly([px-w,py,px-w*.15,py-h,px+w,py]).fill(0x7d827b).stroke(ink);
   g.poly([px-w*.15,py-h,px+w,py,px+w*.1,py]).fill(0x5f645e);
   g.poly([px-w*.15,py-h,px-w*.45,py-h*.55,px-w*.2,py-h*.62,px+w*.05,py-h*.5,px+w*.3,py-h*.6]).fill(0xf2f5f2).stroke({color:INK,width:1});
  };
  peak(x-14,y+6,22,44);peak(x+16,y+10,18,32);
 } else if(biome==='beach'){
  if(n(110)<.35){ // palm
   const px=x+(n(111)-.5)*30,py=y+4;
   g.moveTo(px,py).quadraticCurveTo(px+4,py-14,px+2,py-26).stroke({color:INK,width:4});
   g.moveTo(px,py).quadraticCurveTo(px+4,py-14,px+2,py-26).stroke({color:0x8a6a3a,width:2.4});
   for(const a of [-2.6,-1.9,-1.1,-.4]) g.moveTo(px+2,py-26).quadraticCurveTo(px+2+Math.cos(a)*10,py-30+Math.sin(a)*6,px+2+Math.cos(a)*16,py-22+Math.sin(a)*4).stroke({color:0x3f8a35,width:3.2});
  } else if(n(112)<.5) rock(g,x+(n(113)-.5)*36,y+8,6,5);
 } else if(biome==='desert'){
  g.moveTo(x-34,y+6).quadraticCurveTo(x-6,y-12,x+24,y-2).stroke({color:0xb98d4a,width:1.6});
  g.moveTo(x-18,y+14).quadraticCurveTo(x+6,y+2,x+32,y+10).stroke({color:0xc79b55,width:1.2});
  rock(g,x-22,y+10,6,6);
  if(n(80)<.5){ // dry shrub
   g.moveTo(x+14,y+4).lineTo(x+10,y-6).moveTo(x+14,y+4).lineTo(x+18,y-5).moveTo(x+14,y+4).lineTo(x+14,y-8).stroke({color:0x8a6a3a,width:1.4});
  }
 } else if(biome==='plain'){
  const k=n(90);
  if(k<.35) bush(g,x+(n(91)-.5)*44,y+(n(92)-.5)*16,[0xf2e9a5,0xf3b0c6,0xa9b7f0][Math.floor(n(93)*3)]);
  else if(k<.5) roundTree(g,x+(n(94)-.5)*36,y+4,24,Math.floor(n(95)*5));
  else if(k<.58) stump(g,x+(n(96)-.5)*40,y+6);
  else if(k<.66) rock(g,x+(n(97)-.5)*40,y+8,7,7);
 }
 return g;
}
export function bunker(x:number,y:number){
 const g=new Graphics();
 g.ellipse(x+4,y+7,29,11).fill({color:0x071519,alpha:.4});
 g.poly([x-24,y-7,x+8,y-17,x+26,y-7,x-5,y+5]).fill(0x929883);
 g.poly([x-24,y-7,x-5,y+5,x-5,y+17,x-24,y+5]).fill(0x687164);
 g.poly([x-5,y+5,x+26,y-7,x+26,y+5,x-5,y+17]).fill(0x46554d);
 g.poly([x+2,y+5,x+20,y-2,x+20,y+3,x+2,y+10]).fill(0x17252b);
 g.moveTo(x-16,y-3).lineTo(x-16,y-34).stroke({color:0xb8bca6,width:2});
 g.poly([x-15,y-34,x+1,y-29,x-15,y-24]).fill(0xb75648);
 for(let i=0;i<5;i++)g.roundRect(x-30+i*11,y+14+(i%2)*3,10,5,2).fill(i%2?0x8b876c:0x77785f);
 return g;
}
export function squad(x:number,y:number,color:number,hp?:number){
 const g=new Graphics();
 g.ellipse(x,y+3,27,15).fill({color,alpha:.18}).stroke({color,alpha:.7,width:1});
 for(const [dx,dy] of [[-12,-7],[13,-6],[0,6]]){
  const px=x+dx,py=y+dy;
  g.ellipse(px+3,py+2,8,3).fill({color:0x08141a,alpha:.5});
  g.moveTo(px-3,py).lineTo(px-2,py-10).moveTo(px+4,py).lineTo(px+2,py-10).stroke({color:0x263334,width:4});
  g.roundRect(px-5,py-22,10,13,3).fill(0x73806a);
  g.rect(px-4,py-18,8,7).fill(0x48594e);
  g.circle(px,py-25,4).fill(0xc1ad88);
  g.ellipse(px,py-28,6,4).fill(0x66765b);
  g.moveTo(px+4,py-16).lineTo(px+12,py-22).stroke({color:0x19252b,width:3});
  g.rect(px-6,py-22,3,5).fill(color);
 }
 g.roundRect(x-21,y+21,42,5,2).fill(0x101923);
 g.roundRect(x-20,y+22,40*Math.max(.01,(hp??100)/100),3,1).fill(color);
 return g;
}

// Adventure-map objects. Original code-drawn shapes on the map projection.
const RESOURCE_TINT: Record<string, number> = { metal: 0x9aa7ad, oil: 0x3a3f46, fuel: 0xd08a3c, food: 0x8db35a };
export function pile(x:number,y:number,resource:string){
  const g=new Graphics();const tint=RESOURCE_TINT[resource]??0xb0a27a;
  g.ellipse(x,y+10,24,9).fill({color:0x071319,alpha:.35});
  for(const [dx,dy,w] of [[-10,4,12],[8,6,11],[-1,-6,12]] as const){
    g.poly([x+dx-w,y+dy,x+dx,y+dy-w*.5,x+dx+w,y+dy,x+dx,y+dy+w*.5]).fill(tint);
    g.poly([x+dx-w,y+dy,x+dx,y+dy+w*.5,x+dx,y+dy+w*.5+8,x+dx-w,y+dy+8]).fill(0x5a4a33);
    g.poly([x+dx,y+dy+w*.5,x+dx+w,y+dy,x+dx+w,y+dy+8,x+dx,y+dy+w*.5+8]).fill(0x3e3324);
  }
  return g;
}
export function chest(x:number,y:number){
  const g=new Graphics();
  g.ellipse(x,y+10,20,8).fill({color:0x071319,alpha:.35});
  g.poly([x-16,y,x,y-8,x+16,y,x,y+8]).fill(0xe5b65a);
  g.poly([x-16,y,x,y+8,x,y+20,x-16,y+12]).fill(0x8a5a2b);
  g.poly([x,y+8,x+16,y,x+16,y+12,x,y+20]).fill(0x6b4320);
  g.rect(x-2,y+6,4,6).fill(0xf6dc8c);
  g.moveTo(x-16,y+4).lineTo(x,y+12).lineTo(x+16,y+4).stroke({color:0xc49a3c,width:2});
  return g;
}
export function mine(x:number,y:number,resource:string,owner:number|null){
  const g=new Graphics();
  g.ellipse(x,y+10,28,10).fill({color:0x071319,alpha:.35});
  g.poly([x-24,y+6,x-8,y-12,x+14,y-10,x+24,y+6,x,y+16]).fill(0x4b524c);
  g.poly([x-8,y+2,x+2,y-8,x+12,y+2,x+2,y+10]).fill(0x161e22);
  g.moveTo(x-10,y+4).lineTo(x-2,y-14).lineTo(x+6,y+4).stroke({color:0xb9a67c,width:3});
  g.circle(x+14,y+8,4).fill(RESOURCE_TINT[resource]??0xaaaaaa);
  g.moveTo(x+18,y-2).lineTo(x+18,y-30).stroke({color:0xc3d0c6,width:2});
  g.poly([x+19,y-30,x+33,y-25,x+19,y-20]).fill(owner??0xa7aeb5);
  return g;
}

// Vehicle stacks for the tactical field (original code-drawn shapes).
export function vehicle(x:number,y:number,color:number,kind:string,ratio:number){
  const g=new Graphics();
  g.ellipse(x,y+3,30,15).fill({color,alpha:.18}).stroke({color,alpha:.7,width:1});
  if(kind==="armor"){
    g.ellipse(x+2,y+6,24,8).fill({color:0x08141a,alpha:.45});
    g.poly([x-24,y,x-4,y-11,x+24,y-2,x+4,y+9]).fill(0x5f6e55);
    g.poly([x-24,y,x+4,y+9,x+4,y+15,x-24,y+6]).fill(0x3b4637);
    g.poly([x+4,y+9,x+24,y-2,x+24,y+4,x+4,y+15]).fill(0x2e372b);
    g.poly([x-10,y-6,x,y-12,x+12,y-6,x+2,y]).fill(0x75846a);
    g.moveTo(x+4,y-7).lineTo(x+26,y-16).stroke({color:0x2a332a,width:4});
    g.rect(x-9,y-8,4,4).fill(color);
  } else {
    g.ellipse(x,y+8,22,6).fill({color:0x08141a,alpha:.45});
    g.circle(x-12,y+6,6).fill(0x2c3430);g.circle(x+8,y+8,6).fill(0x2c3430);
    g.poly([x-16,y+2,x+12,y+4,x+14,y-2,x-14,y-4]).fill(0x66745f);
    g.moveTo(x-2,y-2).lineTo(x+24,y-20).stroke({color:0x2a332a,width:5});
    g.rect(x-14,y-6,5,4).fill(color);
  }
  g.roundRect(x-21,y+21,42,5,2).fill(0x101923);
  g.roundRect(x-20,y+22,40*Math.max(.01,ratio),3,1).fill(color);
  return g;
}
