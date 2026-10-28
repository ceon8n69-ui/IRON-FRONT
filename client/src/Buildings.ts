import { Container, Graphics } from "pixi.js";
import type { Building } from "./store";

// Original code-drawn assets. Coordinates share the map's isometric projection.
export type BuildingVisual = { node: Container; animate: (seconds: number) => void };
export function createBuilding(b: Building): BuildingVisual {
  const node = new Container();
  const g = new Graphics();
  node.addChild(g);
  const stage = b.level >= 8 ? 4 : b.level >= 5 ? 3 : b.level >= 3 ? 2 : 1;
  const roof = [0, 0x899990, 0x9ba99b, 0xa7b1a3, 0xbac2b0][stage];
  const box = (x: number, y: number, w: number, d: number, h: number, top = roof) => {
    y = -y;
    g.poly([x-w,y-d,x,y-d-w*.48,x+w,y-d,x,y-d+w*.48]).fill(top);
    g.poly([x-w,y-d,x,y-d+w*.48,x,y-d+w*.48+h,x-w,y-d+h]).fill(0x53676b);
    g.poly([x,y-d+w*.48,x+w,y-d,x+w,y-d+h,x,y-d+w*.48+h]).fill(0x30494f);
    g.moveTo(x-w,y-d).lineTo(x,y-d+w*.48).lineTo(x+w,y-d).stroke({color:0xc0c9b4,alpha:.35,width:1});
  };
  g.ellipse(7,8,41,17).fill({color:0x071319,alpha:.4});
  g.poly([-43,0,0,-22,43,0,0,22]).fill(0x737b6b).stroke({color:0x939b81,width:1});
  // Concrete seams and hazard-marked entrances.
  g.moveTo(-34,2).lineTo(2,19).moveTo(0,-18).lineTo(35,0).stroke({color:0x4d5a53,width:1});
  const radar = new Graphics();
  const smoke = new Container();
  const crane = new Container();
  const pump = new Graphics();
  if (b.status === "building") {
    box(0,10,29,15,10,0x5e6861);
    for (const x of [-25,0,25]) {
      g.moveTo(x,7).lineTo(x,-34).stroke({color:0xc49c57,width:2});
    }
    g.moveTo(-25,-16).lineTo(25,-16).moveTo(-25,-33).lineTo(25,-33).moveTo(-25,7).lineTo(25,-33).stroke({color:0x8d9b91,width:1.5});
    g.rect(-34,-60,4,64).fill(0xc5a35f);
    const arm = new Graphics().moveTo(-30,-59).lineTo(32,-59).lineTo(-24,-70).lineTo(-30,-59).stroke({color:0xe5b65a,width:2});
    crane.addChild(arm); node.addChild(crane);
    g.rect(-18,10,36,5).fill(0x24343c);
    for(let i=0;i<6;i++) g.poly([-18+i*6,10,-14+i*6,10,-17+i*6,15,-21+i*6,15]).fill(0xd8ac58);
  } else if (b.kind === "hq") {
    box(0,28,32,5,29);
    box(-5,51,21,5,23);
    g.poly([-17,-50,-5,-56,7,-50,-5,-44]).fill(0x344c53);
    for(let i=0;i<4;i++) {
      g.rect(-25+i*6,-15+i*2.8,3,5).fill(0x91b9bf);
      g.rect(5+i*5,-5-i*2.5,3,5).fill(0x779da6);
    }
    g.poly([-5,-1,3,3,3,15,-5,11]).fill(0x1c3038);
    g.moveTo(0,-56).lineTo(0,-75).stroke({color:0xc3d0c6,width:2});
    g.poly([1,-75,19,-69,1,-64]).fill(0xe5b65a);
    radar.position.set(16,-49); node.addChild(radar);
  } else if (b.kind === "power") {
    box(8,19,25,3,20,0x718680);
    for(const x of [-23,-8]) {
      g.rect(x-6,-43,12,43).fill(0x6d8581);
      g.rect(x+2,-43,4,43).fill(0x3c555b);
      g.ellipse(x,-43,6,3).fill(0xa9b4a1);
      g.rect(x-6,-37,12,5).fill(0xe2b45c);
    }
    for(let i=0;i<4;i++) g.moveTo(5+i*6,-18+i*2.8).lineTo(5+i*6,-8+i*2.8).stroke({color:0x233b44,width:3});
    smoke.position.set(-18,-47); node.addChild(smoke);
  } else if (b.kind === "barracks") {
    box(0,22,34,2,22,0x6d8378);
    g.poly([-34,-24,0,-44,34,-24,0,-8]).fill(0x8b9a85);
    g.poly([0,-44,34,-24,0,-8]).fill(0x617b71);
    for(let i=0;i<5;i++) g.moveTo(-26+i*6,-22+i*2.8).lineTo(-26+i*6,-11+i*2.8).stroke({color:0x243b3e,width:3});
    g.poly([9,-9,19,-14,19,1,9,6]).fill(0x253a3e);
    g.moveTo(-35,-4).lineTo(-35,-37).stroke({color:0xb5c2ad,width:2});
    g.poly([-34,-37,-21,-32,-34,-27]).fill(0x4c9ce5);
  } else if (b.kind === "quarry") {
    g.poly([-32,1,-14,-15,24,-9,35,4,4,17]).fill(0x3f4b47);
    for(let i=0;i<4;i++) {
      const x=-20+i*12;
      g.poly([x,7,x+2,-4,x+10,-10,x+17,1,x+12,10]).fill(i%2?0x899083:0x69796f);
    }
    box(-15,28,16,0,14,0xb2a275);
    g.poly([-11,-22,19,-7,19,-1,-11,-16]).fill(0x354b4c).stroke({color:0xb1a475,width:2});
    g.moveTo(15,-6).lineTo(15,9).stroke({color:0x869581,width:3});
    g.circle(-20,-8,4).fill(0x253b40);
  } else if (b.kind === "refinery") {
    box(-17,18,18,1,18,0x6d8580);
    for(const x of [5,23]) {
      g.rect(x-9,-30,18,34).fill(0x728b85);
      g.ellipse(x,4,9,4).fill(0x536f6e);
      g.ellipse(x,-30,9,5).fill(0xb0b9a8);
      g.rect(x+4,-28,4,29).fill(0x415e60);
    }
    g.moveTo(-19,-31).lineTo(-19,-49).lineTo(13,-49).lineTo(13,-34).stroke({color:0xb9a67c,width:3});
    smoke.position.set(-19,-52); node.addChild(smoke);
  }
  else if (b.kind === "oil_well") {
    g.poly([-30,4,0,-12,30,4,0,20]).fill(0x3b4642);
    // Pump jack: frame, beam, horse head.
    g.moveTo(-12,6).lineTo(-2,-28).lineTo(8,6).stroke({color:0x8a9688,width:3});
    pump.position.set(-2,-30); node.addChild(pump);
    box(18,16,9,0,10,0x7a6f55);
    g.rect(-27,-6,8,12).fill(0x2b3a3f);g.ellipse(-23,-6,4,2).fill(0x8f9a8c);
  } else if (b.kind === "farm") {
    for(let i=0;i<4;i++){const y=-2+i*6;g.poly([-36+i*4,y,-6+i*4,y-14,6+i*4,y-8,-24+i*4,y+6]).fill(i%2?0x7f9b4f:0x6c8a43);}
    box(16,22,14,0,14,0x9b7f55);
    g.poly([2,-30,16,-38,30,-30,16,-22]).fill(0xb3563f);
    g.rect(-30,-32,6,24).fill(0xa9ad9a);g.ellipse(-27,-32,4,2).fill(0xd2d4c3);
  } else if (b.kind === "warehouse") {
    box(0,18,36,4,18,0x7d8a7c);
    g.poly([-36,-20,0,-38,36,-20,0,-2]).fill(0x93a08f);
    for(let i=0;i<3;i++) g.poly([6+i*9,-6+i*-4,13+i*9,-9+i*-4,13+i*9,4+i*-4,6+i*9,7+i*-4]).fill(0x2f4247);
    for(let i=0;i<3;i++) box(-26+i*9,-14+i*4,4,0,5,0xc29b52);
  } else if (b.kind === "watchtower") {
    for(const x of [-12,12]) g.moveTo(x,6).lineTo(x*.4,-58).stroke({color:0x8b9783,width:3});
    g.moveTo(-12,-10).lineTo(12,-30).moveTo(12,-10).lineTo(-12,-30).stroke({color:0x6d7b70,width:2});
    box(0,62,14,0,8,0x93a08f);
    g.poly([-14,-70,0,-82,14,-70]).fill(0x4c5c58);
    radar.position.set(0,-86); node.addChild(radar);
  } else if (b.kind === "electronics") {
    box(-4,20,30,2,20,0x6e8486);
    g.poly([-30,-22,-4,-36,22,-22,-4,-8]).fill(0x5d7577);
    for(let i=0;i<5;i++) g.rect(-26+i*6,-14+i*2.8,3,4).fill(0x6fd0e5);
    g.rect(14,-46,8,30).fill(0x617a7c);g.ellipse(18,-46,4,2).fill(0xb4c0b0);
    for(let i=0;i<3;i++) g.circle(-14+i*9,-30+i*-1,2).fill(0x4c9ce5);
    smoke.position.set(18,-50); node.addChild(smoke);
  } else if (b.kind === "repair") {
    box(0,18,32,2,18,0x7c8a80);
    g.poly([-30,-18,0,-34,30,-18,0,-2]).fill(0x8d9a8c);
    g.poly([4,-6,22,-15,22,6,4,15]).fill(0x24363c);
    g.rect(-20,-30,10,3).fill(0xe5b65a);g.rect(-16.5,-34,3,11).fill(0xe5b65a);
    box(-24,-4,9,0,6,0x5e6f5f);
  }
  if (b.upgrade_ready_at && b.status === "ready") {
    g.rect(30,-62,3,58).fill(0xc5a35f);
    const arm = new Graphics().moveTo(32,-61).lineTo(-14,-61).lineTo(26,-70).lineTo(32,-61).stroke({color:0xe5b65a,width:2});
    crane.addChild(arm); node.addChild(crane);
  }
  if(stage>1 && b.status === "ready") {
    for(let i=1;i<stage;i++) box(-34+i*11,-7,5,0,8,0x91a49b);
    g.moveTo(-41,8).lineTo(0,28).lineTo(41,8).stroke({color:stage===4?0xe5b65a:0x8caaac,width:stage});
  }
  const puffs = Array.from({length:4},()=>new Graphics().circle(0,0,5).fill(0xd4d7c5));
  smoke.addChild(...puffs);
  const cable = new Graphics(); crane.addChild(cable);
  const animate = (t: number) => {
    radar.clear().ellipse(0,0,10,4).stroke({color:0xb9c9b7,width:1.5})
      .moveTo(0,0).lineTo(Math.cos(t)*10,Math.sin(t)*4).stroke({color:0xe5b65a,width:2});
    puffs.forEach((p,i)=>{ const phase=(t*.2+i/4)%1; p.position.set(phase*14,-phase*27); p.scale.set(.4+phase);p.alpha=(1-phase)*.22; });
    pump.clear().moveTo(-18,0).lineTo(16,0).stroke({color:0xb9a67c,width:3}).circle(-18,0,0).fill(0);
    pump.rotation = Math.sin(t*1.4)*.25;
    pump.poly([-22,-4,-14,-4,-14,10,-22,10]).fill(0xd8ac58);
    cable.clear().moveTo(14+Math.sin(t*.6)*12,-59).lineTo(14+Math.sin(t*.6)*12,-20).stroke({color:0xc3ba8c,width:1});
  };
  animate(0);
  return {node, animate};
}
