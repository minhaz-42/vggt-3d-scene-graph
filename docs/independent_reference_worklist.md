# Independent reference — human-verification worklist

Drafted + adversarially verified from the raw RGB frames by two independent passes per scene (workflow `independent-reference-draft`), then **HUMAN-VERIFIED on 2026-06-30** — the human pass removed ambiguous detections (window in room/desk/desk2; cup/bottle/picture in desk2; door/trash can in fr3). The verified multisets are in `configs/evaluation/independent_labels.json` (`label_source: vlm-drafted-human-verified`); the per-scene draft evidence below is retained as the provenance record.

## tum_rgbd_freiburg1_room
_confidence: medium — frames are heavily motion-blurred; structural items and the two monitors/keyboards are clear, but the chair and the back-desk electronics cluster count are the weakest judgments._

**Multiset (19 objects):** `{"wall": 1, "floor": 1, "desk": 1, "door": 1, "window": 1, "cabinet": 1, "chair": 1, "monitor": 2, "keyboard": 2, "book": 1, "cup": 1, "box": 1, "bag": 1, "unknown object": 4}`

Per-label evidence:
- **unknown object** ×4 — Open ThinkPad laptop with screen on (frames 1,2,3,10); small dark phone/PDA near the pen cup (frames 1,3,4,9); yellow-green tennis ball on the far desk (frames 1,3,10); cluster of scattered small electronics/external drives on the back desk (frames 1,2,3,10). None map to vocabulary.
- **monitor** ×2 — Large Samsung LCD monitor (frames 1,3-9) plus a second dark monitor on opposite/left side of desk (frames 1,2,10).
- **keyboard** ×2 — Black external keyboard right of/below the right monitor in frame 1; a second keyboard on the far back desk in frames 2,10.
- **wall** ×1 — White painted brick wall behind desk, all frames (clearest frames 3-8).
- **floor** ×1 — Wooden floor under and beside the desk, frames 1,4,5,6,7,8,10.
- **desk** ×1 — Light L-shaped office desk holding all equipment; one connected structure, frames 1-10.
- **door** ×1 — Wood-paneled vertical door/cabinet panel at far left, frames 5,6,7,8.
- **window** ×1 — Window opening with horizontal frame/blind at top-left, frames 4,9,10.
- **cabinet** ×1 — Dark navy multi-drawer pedestal cabinet at lower left, frames 5,6,7,8.
- **chair** ×1 — Dark caster/base at bottom of frame 7 and dark mesh seat surface bottom-right of frame 10 (partial, low confidence).
- **book** ×1 — Stack of papers/notebooks left of the monitor, frames 3,4,5,6,7,8,9.
- **cup** ×1 — Pen/pencil holder cup on the desk beside the monitor, frames 3,4,5,6,8,9.
- **box** ×1 — Yellow/white cardboard box standing on the cabinet/desk edge, frames 4,5,6,7,8.
- **bag** ×1 — Flat black 'ROS/SONY' laptop case/sleeve with carry strap lying on the desk, frames 2,3,4,5,6,7,8,9,10.

Adversarial corrections applied:
- Confirmed wall/floor/desk each as single structures (count 1) — no change.
- Window evidence corrected: also visible in frame 10, not only frames 4 and 9.
- Kept monitor=2: independently verified a second dark monitor slab at the left edge in frames 1,2,10 distinct from the Samsung.
- Kept keyboard=2: verified separate keyboards (frame 1 near right monitor; back desk in frames 2,10).
- Kept chair=1 with low confidence: caster in frame 7 plus mesh seat bottom-right of frame 10.
- Did NOT add 'bottle': the light cylindrical object at left (frames 5-8) is a rolled paper/poster, not a bottle.
- Kept unknown object=4 (laptop, phone, tennis ball, electronics cluster) — all salient and out-of-vocabulary; declined to inflate the blurry back-desk cluster into multiple counts.

## tum_rgbd_freiburg1_desk
_confidence: medium — desk items are clear but heavy motion blur makes exact monitor count (3 vs 4) and a possible 2nd keyboard genuinely uncertain._

**Multiset (21 objects):** `{"monitor": 3, "keyboard": 1, "desk": 1, "book": 3, "cup": 2, "chair": 1, "door": 1, "window": 1, "box": 2, "wall": 1, "floor": 1, "unknown object": 4}`

Per-label evidence:
- **unknown object** ×4 — (1) White desk telephone with coiled handset cord, frames 7-10. (2) Black gamepad/controller, frames 8-10 lower-left. (3) Round red device (tape dispenser), frames 7-10 near the phone. (4) Light-gray computer mouse on the desk beside the keyboard, clearly visible frames 1-7 (MISSED by draft). None are in the controlled vocabulary.
- **monitor** ×3 — Frame 1: left black flat-panel + center silver-bezel monitor. Frames 5-10: wide black widescreen monitor in foreground. Frame 6 shows multiple screens around the desk corner; conservatively 3 distinct flat-panels (foreground black, center silver, plus a far black one).
- **book** ×3 — Frames 7-10: teal 'Multiple View Geometry' textbook (lower-left) and a separate blue/purple bound book stacked above it. Frames 1-6: a thin dark-blue booklet near the center monitor. Three distinct bound volumes.
- **cup** ×2 — Frames 5-10: white ceramic mug standing on the desk. Frames 6-10: a separate round pen-holder cup filled with pens/markers. Two cup-shaped containers.
- **box** ×2 — Frames 7-10: small printed cardboard cartons amid the desk clutter near the pen holder (a white/blue printed box plus an adjacent smaller carton).
- **keyboard** ×1 — One light-gray full-size keyboard in front of the foreground monitor, present in every frame 1-10.
- **desk** ×1 — One continuous L-shaped light/white office desk on which everything sits; the right surface in frames 3-4 is the same desk corner.
- **chair** ×1 — Frames 6-10: light-tan wooden chair back in the upper-left background behind the desk.
- **door** ×1 — Frames 6-10: tall light-colored door/panel in the left background of the room.
- **window** ×1 — Frames 6-10: vertical blinds in the upper-left background behind the desk.
- **wall** ×1 — White painted wall forming the background behind the monitors in frames 1-6.
- **floor** ×1 — Wooden floor visible under/beside the desk in lower portions of frames 2-5 and 9-10.

Adversarial corrections applied:
- Added a 4th unknown object: light-gray computer mouse on the desk next to the keyboard (clearly visible frames 1-7), missed by the draft; bumped unknown object count 3->4.
- Kept monitor=3 as a conservative floor; frame 6 hints at a possible 4th screen but it is too ambiguous/blurred to assert confidently.
- Verified keyboard=1: a possible second dark keyboard at the back in frame 6 is too indistinct to count; left at 1.
- Confirmed all other draft entries (desk, book=3, cup=2, chair, door, window, box=2, wall, floor) against my own frame review; no over/undercounts found.
- Confirmed the three draft unknown objects (telephone, gamepad, red tape dispenser) are correctly out-of-vocab and not double-counted across frames.

## tum_rgbd_freiburg1_desk2
_confidence: medium — frames are heavily motion-blurred; structures/desks/monitors/lamp/books are clear, but cup x2, box x2, and bottle instance-merging carry genuine ambiguity._

**Multiset (27 objects):** `{"wall": 1, "floor": 1, "window": 1, "door": 1, "desk": 2, "chair": 1, "lamp": 1, "monitor": 3, "keyboard": 1, "book": 3, "cup": 2, "bottle": 1, "box": 2, "picture": 2, "unknown object": 5}`

Per-label evidence:
- **unknown object** ×5 — (1) Black-and-white checkerboard calibration pattern on left desk (f1,f2,f3,f5); (2) beige desktop telephone with coiled cord (f7 faint, f10); (3) black game controller/gamepad (f9,f10); (4) round red-and-blue device, small speaker/radio (f8,f9,f10); (5) black computer mouse (f6 near keyboard, f9 bottom-left) — mouse not in vocabulary.
- **monitor** ×3 — Multi-monitor workstation: left silver-framed panel (f1,f5,f6); center black panel and a back-left smaller monitor (f6,f7); large black monitor at right (f7,f8,f9). At least 3 distinct displays.
- **book** ×3 — Blue stapled booklet (f1,f2,f3,f5); 'Multiple View Geometry' teal/blue textbook (f8,f9,f10); blue 'Hennessy' architecture book on left desk (f8,f9). White loose papers are not counted as books.
- **desk** ×2 — Two light-colored office desk surfaces pushed into an L; seam visible in f1,f3,f5,f6,f7. These are office desks, not freestanding tables.
- **cup** ×2 — White pen-holder cup with pens (f8,f9,f10) and a separate translucent plastic drinking cup behind it (f8) / white cup top-right (f10).
- **box** ×2 — (1) Cardboard 'CHUNK' cookie carton standing on desk f8,f9,f10. (2) Red plastic crate/tray at right edge of desk in f2,f3,f4.
- **picture** ×2 — Standing Santa greeting card on desk (f10, also small card behind monitor f7); separate glossy printed photo lying flat (f9,f10).
- **wall** ×1 — White wall with painted darker lower band behind desks; f1-f8.
- **floor** ×1 — Wooden parquet floor at bottom edge of f5, f9, f10.
- **window** ×1 — Large window, brown wooden frame, horizontal blinds, blown-out daylight; f2,f3,f4,f6,f7.
- **door** ×1 — Tall wood-grain panel (door/cabinet face) behind desk in f7 and f8.
- **chair** ×1 — Faint light-wood chair back behind the left desk in f7.
- **lamp** ×1 — Articulated desk lamp with metal arm extending over the desk; clearly visible f2,f3,f4 and arm in f5/f6. MISSED by draft.
- **keyboard** ×1 — Light/grey keyboard in front of monitors; f6, f8(right), f9(top-right), f10(right).
- **bottle** ×1 — Clear plastic bottle with red cap; standing on right desk f2,f3,f4. (Same bottle likely relocated lying down in f8/f9; counted once conservatively.)

Adversarial corrections applied:
- Remapped 'table' x2 -> 'desk' x2: these are office desks in a workstation, and 'desk' is the more specific in-vocab label.
- ADDED 'lamp' x1: articulated desk lamp clearly visible in f2,f3,f4 with arm over desk; missed by draft.
- Increased 'cup' 1 -> 2: pen-holder cup plus a separate translucent drinking cup are both visible in f8.
- Increased 'box' 1 -> 2: added the red plastic crate/tray at the right desk edge in f2,f3,f4 in addition to the CHUNK cookie carton.
- Increased 'unknown object' 4 -> 5: added a black computer mouse (f6, f9), which is salient and out-of-vocabulary.
- Kept book x3 but reassigned the third book to the blue 'Hennessy' book rather than a white report; loose white papers are not books and are not in the vocabulary, so not counted.
- Kept bottle x1 conservatively (standing bottle f2-4 likely the same bottle seen lying down f8-9 on a moving trajectory).

## tum_rgbd_freiburg2_xyz
_confidence: medium — core in-vocab objects are unambiguous; uncertainty is in the cluttered, motion-blurred back-left pile where the exact split of cans/containers and the book-vs-binder mapping is hard to pin to an exact integer._

**Multiset (18 objects):** `{"desk": 1, "floor": 1, "monitor": 1, "keyboard": 1, "cup": 1, "plant": 1, "book": 3, "unknown object": 9}`

Per-label evidence:
- **unknown object** ×9 — Non-vocab salient items, each a distinct physical instance: (1) white desk telephone with coiled handset, right of monitor, all frames; (2) black computer mouse on desk, all frames; (3) brown teddy bear with yellow/black ball behind monitor (frame_000001, frame_000003, frame_000010); (4) round black tape reel/dispenser on gray X-shaped stand, left (frame_000003-000010); (5) blue/green desk globe, right of keyboard (frame_000004, frame_000007, frame_000009); (6) black-and-white checkerboard calibration target at right edge (frame_000001, frame_000004, frame_000007); (7) red Coca-Cola can, lower-left of desk (frame_000002 onward); (8) yellow/orange beverage can in back-left clutter (frame_000002, frame_000003, frame_000006); (9) small white/silver cylindrical container/cup beside the yellow can in back-left clutter (frame_000001, frame_000003, frame_000007).
- **book** ×3 — Left of desk: a flat stack of two distinct bound volumes (dark/blue spine + light/white spine) plus one upright orange binder/folder leaning on the tape stand (frame_000003, frame_000006, frame_000009).
- **desk** ×1 — Single light-wood desk surface fills the foreground in all 10 frames; the structure holding every object.
- **floor** ×1 — Gray industrial concrete floor in the background beyond the desk in every frame (clear in frame_000001, frame_000005, frame_000010).
- **monitor** ×1 — One silver Samsung LCD monitor, screen off, centered on the desk in all frames (frame_000001-000010).
- **keyboard** ×1 — One black/silver keyboard in front of the monitor in all frames (frame_000001-000010).
- **cup** ×1 — One white mug with blue rim on the right of the desk in all frames (frame_000001, frame_000008, frame_000010).
- **plant** ×1 — Green leafy plant fronds entering from the left edge in frames 2-10 (clearest frame_000005, frame_000009, frame_000010).

Adversarial corrections applied:
- Kept book=3 but re-scoped evidence: the count is 2 flat bound volumes + 1 upright orange binder; flagged the binder as the ambiguous third instance rather than asserting 3 clean books.
- Raised unknown object 8 -> 9: the draft's back-left item (8) lumped a yellow can and a small cylindrical container together; I see these as two distinct physical instances (yellow can + small white tin/cup).
- Verified no bottle present (the cans are unknown, the white mug is cup) — correctly absent from inventory.
- Confirmed all single-surface/single-instance items (desk, floor, monitor, keyboard, cup, plant) are count 1 — same physical object tracked across the 10-frame trajectory, not multiplied per frame.

## tum_rgbd_freiburg3_long_office_household
_confidence: medium — desk-top inventory and furniture are clear; bottle count (6) and the background door/cabinet are the main residual uncertainties due to clutter and low background resolution._

**Multiset (23 objects):** `{"desk": 1, "chair": 2, "floor": 1, "wall": 1, "cabinet": 1, "door": 1, "bottle": 6, "cup": 3, "book": 1, "box": 1, "bag": 1, "trash can": 1, "unknown object": 3}`

Per-label evidence:
- **bottle** ×6 — Across all frames: 2 clear plastic water bottles (red Vittel-style labels) upper-left shelf, 1 green tall soda bottle upper shelf, 1 green soda bottle in the mid-desk back cluster, 1 dark brown glass beer-style bottle, and 1 tall clear/green bottle far right behind the Lidl bag. Six distinct instances tracked consistently.
- **cup** ×3 — Right side of desk frames 1-10: one white coffee cup on a white saucer, one small dark-blue plastic cup beside it, and a small white cup/dish to its right. Three small drinking-vessel instances.
- **unknown object** ×3 — Salient non-vocab desk items: (1) blue inflatable Earth globe/balloon on upper-left shelf (all frames); (2) large yellow foam die/cube center-left of desk (all frames); (3) red plastic basket/airplane-shaped toy mid-desk right (all frames). Three distinct instances.
- **chair** ×2 — All frames: one maroon/purple molded swivel office chair (foreground left) and one yellow wooden-seat swivel office chair (right). Two distinct instances. Far-background blurry chairs not confidently distinguishable, not counted.
- **desk** ×1 — All frames: the long light-topped office desk in the foreground (two tops butted together with a cardboard partition divider standing on it). One surface per large-surface rule.
- **floor** ×1 — All frames: grey linoleum office floor under desk and chairs.
- **wall** ×1 — Frames 1-10: white/light far wall of the open-plan office behind/around the desk (top corners and background).
- **cabinet** ×1 — Top-left/top background frames 1-5,10: white wall-mounted cupboards/cabinets on the far wall behind the desk.
- **door** ×1 — Background frames 5-10: a darker doorway/door opening in the far wall, upper area. Lower confidence but a distinct opening is visible.
- **book** ×1 — Center of desk all frames: a purple/dark glossy magazine ('Katalog'-style cover) lying flat on the desktop.
- **box** ×1 — Center-left of desk all frames: an upright striped (red/yellow/green) container/pen-holder box standing on the desktop.
- **bag** ×1 — Right side of desk all frames: a white/yellow/blue 'Lidl' branded plastic bag standing on the desk.
- **trash can** ×1 — Bottom-left foreground floor, clearest frames 8-10 (partly visible earlier): an orange plastic bucket/bin on the floor beside the maroon chair.

Adversarial corrections applied:
- Removed the 'plant' entry (draft listed count 0) — zero-count items do not belong in the multiset; no plant is visible.
- Verified and kept bottle count at 6 after independently re-counting back-shelf and desk clusters; a possible 7th small bottle in the center cluster is too ambiguous to count, so stayed conservative.
- Confirmed door at count 1 but lowered confidence — the background opening is real but small/blurry.
- Confirmed all other draft entries (desk, 2 chairs, floor, wall, cabinet, 3 cups, book, box, bag, trash can, 3 unknown objects) match my independent read; no other changes.

