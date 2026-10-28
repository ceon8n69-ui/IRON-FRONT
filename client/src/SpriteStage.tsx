import { useEffect, useRef } from "react";
import { Application } from "pixi.js";
import { unitSprite } from "./Units";

/** Build-time helper page (?sprite=<art>&faction=<id>): one unit on a transparent canvas for tools/render-units.mjs. */
export function SpriteStage() {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const app = new Application();
    (async () => {
      await app.init({ width: 128, height: 112, backgroundAlpha: 0, antialias: true, resolution: 2, autoDensity: true, preserveDrawingBuffer: true });
      host.current!.appendChild(app.canvas);
      const sprite = unitSprite(params.get("sprite") ?? "rifleman", params.get("faction") ?? undefined, params.get("side") ?? "player", 1);
      sprite.removeChildAt(sprite.children.length - 1);
      sprite.scale.set(1.45);
      sprite.position.set(64, 92);
      app.stage.addChild(sprite);
      app.render();
      (window as unknown as { __spriteReady: boolean }).__spriteReady = true;
    })();
    return () => app.destroy(true);
  }, []);
  return <div id="sprite" ref={host} style={{ width: 128, height: 112, background: "transparent" }} />;
}
