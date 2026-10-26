# Commander art v1

Generated with the built-in imagegen tool for IRON FRONT. Original fictional characters; no existing franchise characters or real insignia were requested. Production files are WebP derivatives with proportional downsampling and compression; artwork was not composited or retouched. Original generated PNGs remain in the creation workspace. These assets are illustrations, not equipment-reactive 3D models.

Stable paths: `client/public/art/commanders/{raven,valkyrie,titan,phoenix,ghost,storm}-v1.webp`; `client/public/art/equipment/field-module-v1.webp`. Hero IDs, item IDs, ownership and saved progress are unchanged. Total shipped image payload: 426,550 bytes. Portraits load lazily in the selection grid; the active commander portrait loads eagerly.

## Prompt set

Raven prompt:

> Use case: stylized-concept. Project game asset IRON FRONT commander portrait, character General Raven. Single original fictional male commander aged 45, short dark hair with grey temples, composed determined expression, worn charcoal tactical armor and olive command jacket, subtle amber insignia with no real national markings. Premium semi-realistic hand-painted 3D military strategy character illustration, realistic anatomy, detailed fabric and metal, not cartoon. Portrait 2:3 composition, from head to mid thighs, centered, entire head inside frame with generous top margin. Quiet dark blue command hangar background #101923, soft cool rim light and warm key light. No text, no watermark, no UI, no logos, no collage, no real person likeness. Designed to crop cleanly as a portrait card on mobile. Return image asset for use in game project.

Shared prefix for the other five portraits:

> Use case: stylized-concept. IRON FRONT mobile military strategy character portrait. Original fictional character, premium semi-realistic hand-painted 3D military illustration, realistic anatomy, detailed fabric and worn metal, not cartoon. 2:3 vertical, centered head to mid thighs, generous top margin, whole head visible. Dark blue command hangar #101923, cool rim lighting and soft warm key light. Grounded contemporary fictional military clothing. No words, no watermark, no UI, no real insignia, no real person's likeness. Match coherent high-end game portrait art direction.

Append one subject description per generation:

- Valkyrie: Commander Valkyrie: woman age 34 with short ash blonde hair swept to one side, calm observant expression, slate blue lightweight scout armor, high collar and compact binoculars held at waist, headset with small earpiece, subtle blue trims. Professional nonsexual practical silhouette.
- Titan: Colonel Titan: broad powerful man aged 52, shaved head and short greying beard, thoughtful stoic face, heavy reinforced olive and graphite armor, substantial shoulder protection, folded arms low at waist, restrained brass accents, veteran defensive commander.
- Phoenix: Marshal Phoenix: woman age 43 with warm brown skin, black hair in a practical bun, confident empathetic expression, olive logistics officer field coat over light armor, rust orange scarf, carrying a closed rugged supply tablet at hip, small repair and medical utility pouches without red-cross symbol. Professional practical nonsexual silhouette.
- Ghost: Engineer Ghost: man age 32, East Asian appearance, short black hair, focused intelligent face, slim graphite technical field jacket and compact modular armor, protective goggles resting on forehead, muted teal electronics module on chest and small multitool in gloved hand. No hood covering face, no supernatural effects.
- Storm: General Storm: man age 39 with deep brown skin, close-cropped black hair, clean shaven, resolute energetic expression, dark olive armored vehicle crew suit, padded tanker headset resting around neck, weathered slate blue shoulder armor and amber unit patch, hands resting at utility belt.

Module prompt:

> Use case: stylized-concept. Single inventory item asset for IRON FRONT military strategy game: a compact fictional field tactical electronic module, rugged rectangular graphite enclosure, brushed metal edge guards, a small muted green status display, two recessed connectors, olive webbing clip. Premium semi-realistic 3D product illustration. Square composition, device centered with generous empty margin, three-quarter isometric view, crisp readable silhouette. Dark navy #101923 studio backdrop, cool rim and warm key light matching military character art. No writing, no logos, no people, no weapons, no UI, no border, no watermark. Original fictional electronic prop, not real hardware instructions.
