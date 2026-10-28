import { Graphics } from 'pixi.js';

// Original procedural art. Coordinates seed stable detail across chunk changes.
export function noise(q:number,r:number,i:number) {
 let n=Math.imul(q+113,374761393)^Math.imul(r+71,668265263)^Math.imul(i+1,1274126177);
 n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967296;
}
export function surface(x:number,y:number,biome:string,q:number,r:number) {
 const g=new Graphics();if(biome==='unknown')return g;
 for(let i=0;i<25;i++){
  const px=x+(noise(q,r,i*3)-.5)*72,py=y+(noise(q,r,i*3+1)-.5)*36;
  const dry=biome==='desert';
  g.ellipse(px,py,1+noise(q,r,i*3+2)*3,.7).fill({color:dry?0xc4ae78:0x90a276,alpha:.15});
  if(i%4===0&&!dry)g.moveTo(px,py).lineTo(px-1,py-3).moveTo(px,py).lineTo(px+2,py-2).stroke({color:0xa0ad7c,alpha:.23,width:1});
 }
 return g;
}
function rock(g:Graphics,x:number,y:number,w:number,h:number){
 g.ellipse(x+5,y+4,w,5).fill({color:0x0b181c,alpha:.3});
 g.poly([x-w,y,x-w*.5,y-h*.8,x+w*.12,y-h,x+w,y-4,x+w*.45,y+5]).fill(0x66736b);
 g.poly([x-w,y,x-w*.5,y-h*.8,x+w*.12,y-h,x-2,y-2]).fill(0x94a08b);
 g.poly([x+w*.12,y-h,x+w,y-4,x+w*.45,y+5,x-2,y-2]).fill(0x4b5b55);
 g.moveTo(x-w*.5,y-h*.8).lineTo(x+w*.12,y-h).stroke({color:0xb2b8a1,width:1,alpha:.6});
}
export function environment(x:number,y:number,biome:string,q:number,r:number){
 const g=new Graphics();
 if(biome==='forest'){
  for(let i=0;i<7;i++){
   const tx=x+(noise(q,r,i*2)-.5)*65,ty=y-12+i*4,h=24+noise(q,r,i*2+1)*22;
   g.ellipse(tx+7,ty+4,11,4).fill({color:0x071917,alpha:.25});
   g.rect(tx-1.5,ty-11,3,15).fill(0x665a40);
   for(let k=0;k<3;k++){
    const by=ty-6-k*h*.22,w=13-k*3,top=by-h*.48;
    g.poly([tx,top,tx-w,by,tx,by+3,tx+w,by]).fill(k===2?0x49694b:0x35573e);
    g.poly([tx,top,tx,by+3,tx+w,by]).fill(0x263e32);
    g.moveTo(tx,top).lineTo(tx-w,by).stroke({color:0x7d9161,alpha:.45,width:1});
   }
  }
 } else if(biome==='hills'){
  rock(g,x-17,y-5,17,20);rock(g,x+10,y-5,24,36);rock(g,x+25,y+10,12,15);
 } else if(biome==='desert'){
  g.poly([x-35,y+6,x-10,y-8,x+23,y-4,x+37,y+10,x+5,y+15]).fill({color:0xb7a273,alpha:.3});
  g.moveTo(x-35,y+6).quadraticCurveTo(x-5,y-15,x+23,y-4).stroke({color:0xd5be89,width:1,alpha:.4});
  rock(g,x-22,y+10,6,6);
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
