# Expanded reference — 23 VLM-drafted scenes (spot-check worklist)

Two independent passes (draft+verify) from frames; **pending human verification**. The 5 gold scenes are in independent_labels.json.

## tum_rgbd_freiburg1_360  (_medium — frames are heavily motion-blurred; desk-cluster and_)
`{"desk": 1, "table": 1, "chair": 1, "keyboard": 1, "book": 1, "cup": 1, "bag": 1, "lamp": 1, "cabinet": 1, "picture": 1, "wall": 1, "floor": 1, "ceiling": 1, "unknown object": 8}`  (21 objects)
- unknown object ×8 — (1) brown teddy bear on chair, frames 1,3; (2) black game controller/gamepad on desk, frames 1-2; (3) red+white motorized device/robot on floor, frames 3,8,9,10; (4) whiteboard on wall, frames 4-9 (not in vocab); (5) white standing pedestal fan, frames 8-10 (not in vocab); (6,7) two wall/rail-mounted pink-black motion-capture cameras, two visible simultaneously in frame 6; (8) small red+white electronic device on a mousepad on the desk, frames 1-2 (distinct from the floor robot).
- desk ×1 — Frames 1-2: large white desk in foreground holding papers, keyboard, pen cup, book, gamepad; same edge bottom-left of frame 3.
- table ×1 — Frames 3,4,8,9,10: small light-wood table/stand against the wall under the whiteboard.
- chair ×1 — Frames 1,3: dark/grey chair behind the desk on which the teddy bear sits (legs/seat visible).
- keyboard ×1 — Frames 1-2: silver/white computer keyboard on the left edge of the desk.
- book ×1 — Frames 1-2: blue softcover book lying near the front-left corner of the desk.
- cup ×1 — Frame 1: cylindrical pen-holder cup full of pens/markers on the desk (mapped to cup).
- bag ×1 — Frames 3,4,8,9,10: dark cloth/bag stored on the floor beneath the small wooden table (this is the dark rectangular mass the draft wrongly called a 'monitor').
- lamp ×1 — Frames 4-5: tall thin floor-standing pole/stand rising in front of the wall left of the whiteboard (ambiguous floor lamp vs stand, mapped to lamp).
- cabinet ×1 — Frames 9-10: large white box-like cabinet/appliance (fridge-like) against the wall on the right.
- picture ×1 — Frames 4,6: poster/printed sheet taped to the wooden wall left of the whiteboard.
- wall ×1 — Wood-paneled wall visible throughout frames 3-10; counted once.
- floor ×1 — Wooden plank floor visible in nearly every frame; counted once.
- ceiling ×1 — Frames 5-7: white painted ceiling visible at top as the camera tilts up.
- _corr:_ REMOVED monitor (1->0): the dark rectangular mass under the wooden stand in frame 3 is the black cloth/bag stored beneath the table, not a monitor screen (it persists under the table in frames 4,8,9,10).
- _corr:_ ADDED bag (1): the black cloth/bag on the floor under the small wooden table is a distinct in-vocab object (reuses the object the draft mislabeled as monitor).
- _corr:_ INCREASED unknown object 7->8: added the small red+white electronic device sitting on a mousepad on the desk (frames 1-2), which is distinct from the red+white robot on the floor.
- _corr:_ KEPT whiteboard and fan under unknown object (count 0 as own labels) — correct, neither is in the controlled vocabulary.
- _corr:_ KEPT lamp (1) but flagged: the thin vertical pole is ambiguous (could be a tripod/stand for the mocap rig); retained as a salient distinct object mapped to lamp.

## tum_rgbd_freiburg1_xyz  (_medium — most items confirmed across frames; second keyboard_)
`{"person": 1, "chair": 1, "desk": 1, "monitor": 3, "keyboard": 1, "book": 3, "cup": 1, "picture": 1, "box": 2, "wall": 1, "unknown object": 5}`  (20 objects)
- unknown object ×5 — (1) Silver desktop mouse right of keyboard (frames 1,9,10). (2) White corded telephone/handset mid-left (frames 1-8). (3) Wire-mesh pen/pencil holder full of pens/highlighters, center (all frames). (4) Red+blue round desk gadget (tape dispenser/small fan) lower-left (frames 1-8). (5) Black power strip/multi-plug with cables behind keyboard area (frames 1-6). Salient items not in controlled vocabulary.
- monitor ×3 — Central black Samsung LCD (all frames); silver/white-bezel LCD at right edge (frames 9,10); third black LCD on perpendicular far desk (frames 9,10).
- book ×3 — Blue 'Multiple View Geometry' paperback laid flat, thick blue hardcover stacked behind it, and purple/magenta thin booklet on top of the stack (frames 1,2,5).
- box ×2 — White/blue printed carton (coffee/tea box, lower-center, frames 1-8) and a smaller white pill/medicine box with yellow label standing behind the pen holder (frames 1-8).
- person ×1 — Man in white t-shirt seated across the desk; clearly visible frames 1,2,9,10 (face/torso). Same individual.
- chair ×1 — Dark navy empty office swivel chair at left edge; frames 1,2,6,9,10,11. Same chair across trajectory.
- desk ×1 — Continuous white office desk surface holding monitor/keyboard/clutter, spanning all frames; counted as one work surface.
- keyboard ×1 — Beige/cream wired keyboard in front of central monitor (all frames). Could not positively resolve a distinct second keyboard on the far desk; downcounted from 2 to 1.
- cup ×1 — White paper/styrofoam cup standing on desk just left of central monitor (all frames).
- picture ×1 — Glossy photo/postcard of a person in an orange jacket lying flat at lower-left of desk (frames 1-5,7,8).
- wall ×1 — White partition wall plus wooden panel forming the background behind the seated person (frames 1,10,11). One large structure.
- _corr:_ keyboard 2 -> 1: could not positively resolve a distinct second keyboard on the cluttered far-right desk; the keyboard near the right monitor in frame 10 reads as the central keyboard at frame bottom. Downcounted to be conservative.
- _corr:_ Added wall (1): white partition + wooden panel behind the person is a valid in-vocab structure, missed in the draft.
- _corr:_ Confirmed monitor=3, book=3, box=2, unknown object=5 after independent inspection; no hallucinations found among those.
- _corr:_ Confirmed cup, picture, person, chair, desk all =1.

## tum_rgbd_freiburg1_rpy  (_medium — heavy motion blur throughout; monitor=3 and book=2 _)
`{"monitor": 3, "keyboard": 1, "desk": 1, "table": 1, "chair": 1, "trash can": 1, "cup": 1, "book": 2, "floor": 1, "wall": 1, "door": 1, "picture": 1, "plant": 1, "box": 1, "unknown object": 4}`  (21 objects)
- unknown object ×4 — (1) black gamepad/game controller on cardboard, frames 3,4,6,7,8; (2) red/blue stapler-like device, frames 3,6,7,8; (3) camera tripod standing on floor, frames 4,5,6,7; (4) pen-holder container full of pens on the left, frames 2,3,8,9. Plus a computer mouse visible frames 2,8,9,10 (also unknown), folded into this group.
- monitor ×3 — Two black flat-panel monitors on main desk (frames 1,2,8,9,10) plus a small lit screen lower-left in frames 5,6. 3 distinct displays.
- book ×2 — A dark-blue covered manual and a lighter-blue brochure/booklet on the desk, frames 3,4,5,6,7,8,10. Conservatively 2 distinct.
- keyboard ×1 — One light-gray full keyboard centered on desk, frames 1,2,8,9,10.
- desk ×1 — Main white-topped workstation desk dominant in all 10 frames.
- table ×1 — Separate smaller white table surface in background-left, frames 4,5,6,7 (distinct from main desk).
- chair ×1 — Blue office chair on wooden floor across the desk, frames 4,5,6,7.
- trash can ×1 — Blue waste bin on floor by the desk/chair, frames 4,5,6,7.
- cup ×1 — White paper coffee cup near the clutter, frames 2,3,8,9,10. (Pen-holder container moved to unknown object.)
- floor ×1 — Wooden parquet floor, frames 3,4,5,6,7,10.
- wall ×1 — White wall/partition behind and beside the desk, frames 1,5,6,9,10.
- door ×1 — Wooden doorframe/doorway in background of frames 5,6.
- picture ×1 — Sheets/printouts pinned to the wall on the left, frames 5,6.
- plant ×1 — Small green plant amid the desk clutter, frames 3,5,6.
- box ×1 — Black computer tower/cabinet box on the back table, frames 5,6.
- _corr:_ Split draft 'desk' count 2 into desk=1 + table=1 to use distinct in-vocab labels for the two separate surfaces.
- _corr:_ Downcounted cup 2->1: the second 'cup' is a pen-holder container, remapped to unknown object.
- _corr:_ Downcounted book 3->2: only ~2 distinct booklet/manual covers confirmable in this blurry scene.
- _corr:_ Reclassified the black computer tower from 'unknown object' to 'box' (in-vocab).
- _corr:_ Added the computer mouse (in-vocab gap -> unknown object) which the draft omitted; folded into unknown object group.
- _corr:_ Kept unknown object at 4 (tripod, gamepad, stapler-like device, pen holder) after removing the tower (->box) and folding in the mouse.

## tum_rgbd_freiburg1_plant  (_medium — frames are blurry/low-res; the second right-side mo_)
`{"plant": 3, "person": 1, "monitor": 4, "keyboard": 2, "desk": 2, "box": 1, "floor": 1, "wall": 1, "ceiling": 1, "picture": 1, "chair": 1, "cabinet": 1, "shelf": 1, "door": 1, "lamp": 1, "bottle": 1, "bag": 1, "unknown object": 3}`  (27 objects)
- monitor ×4 — Dark monitor on left desk (frames 2,3,4,5); large black monitor on right desk (frames 6-10); a second paler screen to its right (frames 9,10); and a laptop screen on the back desk (frames 7,8,9,10), mapped to monitor since 'laptop' is not in vocab.
- plant ×3 — Foreground large leafy plant in blue glazed pot on white box (all frames); smaller plant in a yellow pot on the back desk (frames 7,8,9,10); a small trailing/hanging plant at far left (frames 1,9,10).
- unknown object ×3 — (1) Brown plush teddy bear on the right desk, frames 1-4; (2) black computer tower under the center desk, frames 5,6,7,8; (3) dark jacket/coat draped over desk/chair, frames 1-4,9,10.
- keyboard ×2 — One keyboard on the left/center desk (frames 3,4,5) and one on the right desk (frames 6-10).
- desk ×2 — Two white office desks with dark legs; left/back desk and right desk, frames 2-10.
- person ×1 — One person in a striped shirt by the back desk/doorway, frames 2,3,9,10.
- box ×1 — White rectangular pedestal/box the foreground potted plant sits on, frames 2-9.
- floor ×1 — Wooden parquet floor across frames 2-10.
- wall ×1 — White walls with posters/papers, frames 1,2,3,9,10.
- ceiling ×1 — Paneled/tiled ceiling at top of frames 1 and 2.
- picture ×1 — Printed posters/flyers taped to the wall (research poster with robot image in frames 9,10; small flyers on left wall frames 1,2,3).
- chair ×1 — Office/visitor chair behind the right desk near the teddy bear, frames 2,3,4.
- cabinet ×1 — Tall white louvered cabinet on the right side of the room, frames 1,2,3,4,5.
- shelf ×1 — Open shelving unit upper-right holding boxes/equipment, frames 1,2.
- door ×1 — Wood-framed glass door in the back wall, partially open with person near it, frames 2,9,10.
- lamp ×1 — Desk lamp / compact-fluorescent fixture on an arm at upper-left, frames 1,2,3.
- bottle ×1 — Yellow bottle/container standing on the back desk, frames 4,7,8,9,10.
- bag ×1 — Dark bag/backpack at the right edge of the right desk, frames 7,9,10.
- _corr:_ Removed the placeholder 'monitor' entry with count 0 (hallucinated/empty).
- _corr:_ Fixed invalid vocab: removed the 'laptop' label (not in vocabulary) and folded the back-desk laptop into 'monitor'.
- _corr:_ Increased monitor 2 -> 4: left monitor + right big monitor + second paler right screen (f9,10) + laptop screen.
- _corr:_ Increased plant 2 -> 3: added the small trailing/hanging plant at far left (frames 1,9,10) alongside the blue-pot and yellow-pot plants.
- _corr:_ Kept person=1, desk=2, keyboard=2, box=1, cabinet=1, shelf=1, chair=1, door=1, lamp=1, bottle=1, bag=1, picture=1, unknown object=3 — all verified against frames.
- _corr:_ Confirmed no single-instance-counted-many-times errors remain; all surfaces (wall/floor/ceiling/desk) within convention.

## tum_rgbd_freiburg1_teddy  (_medium — core scene is unambiguous; second chair, exact box _)
`{"chair": 2, "table": 1, "desk": 1, "cabinet": 2, "shelf": 1, "book": 1, "wall": 1, "floor": 1, "ceiling": 1, "monitor": 1, "window": 1, "picture": 1, "box": 1, "unknown object": 4}`  (19 objects)
- unknown object ×4 — (1) Large brown teddy bear on the chair, central in all 10 frames. (2) Whiteboard on the left wall (frames 1-9). (3) Orange labeled bucket/storage tub on floor right (frames 1-10). (4) Small red toy robot/RC vehicle on the floor at left-center (frames 3,4,5,6,7,8).
- chair ×2 — Main dark office swivel chair holding the teddy (all frames; wheeled base clear in frames 4-7,10). A second low dark chair with casters at far left near the small table (frames 3,7,8). Second chair is lower-confidence but base/wheels visible in frame 8.
- cabinet ×2 — Tall white cabinet center-right with vertical doors (frames 1-9), and a white rolling drawer pedestal on the right (frames 1,2,5,6,7,8,9,10) — no 'drawers' label so mapped to cabinet.
- table ×1 — Small low wooden table against the left wall, partly draped with dark cloth (frames 1,3,4,7,8,9).
- desk ×1 — White desk surface on the far right holding a laptop/monitor (frames 1,5,9,10).
- shelf ×1 — Black open shelf unit upper-right holding ring binders and books (frames 1-9).
- book ×1 — Books and colored ring binders on the black shelf (frames 1-9); one collection.
- wall ×1 — Wood-paneled / white painted walls behind the chair in all frames.
- floor ×1 — Light wooden/tile floor in foreground across all frames, prominent in frames 4-10.
- ceiling ×1 — White ceiling visible at top of frame 3 (and edge of frame 2) where camera tilts up.
- monitor ×1 — Laptop/screen on the right desk surface (frame 10, also frame 9).
- window ×1 — Bright blown-out window/light region upper-left illuminating the scene (frames 1-3,5,7,8,9).
- picture ×1 — Posters/printed sheets taped to the wall on the right side (frames 3,4,7,8,10).
- box ×1 — Cardboard box on the floor next to the orange bucket on the right (frames 4,5,6,9,10); also boxes on top of cabinet in frames 2,3 — counted conservatively as 1.
- _corr:_ Split draft 'desk' (1) into table=1 (left small wooden) + desk=1 (right white surface with laptop) — the right desk surface was being missed entirely.
- _corr:_ Added box=1 — cardboard box on the floor by the orange bucket (frames 4,5,6,9,10) was missed; boxes on top of cabinet also visible (frames 2,3).
- _corr:_ Kept chair=2 but flagged the second chair as lower-confidence; its caster base is visible in frame 8 at far left.
- _corr:_ Kept cabinet=2: tall white cabinet + white rolling drawer pedestal (mapped to cabinet, no 'drawers' label).
- _corr:_ Verified monitor=1 (laptop on right desk, frame 10), window=1, picture=1, ceiling=1 (frame 3) — all confirmed, no hallucinations.
- _corr:_ Kept unknown object=4 (teddy bear, whiteboard, orange bucket, red toy robot) — all real, distinct, and out-of-vocab.

## tum_rgbd_freiburg2_desk  (_medium — desk-surface inventory is clear and well-corroborat_)
`{"desk": 1, "monitor": 1, "keyboard": 1, "book": 2, "cup": 1, "bottle": 2, "plant": 1, "lamp": 1, "box": 1, "floor": 1, "wall": 1, "unknown object": 7}`  (20 objects)
- unknown object ×7 — Seven salient non-vocab items: (1) black computer mouse on desk; (2) white desk telephone with handset; (3) silver/grey roll of duct tape; (4) brown teddy bear plush behind the monitor; (5) yellow perforated/whiffle ball; (6) blue/green world globe on the right of the desk; (7) black-and-white checkerboard calibration target standing at the right in frames 7-10.
- book ×2 — Stack of books/binders with light spines left of keyboard (frames 1-10), plus a separate thick blue atlas-like book right of the phone (frames 1-10).
- bottle ×2 — Two distinct red Coca-Cola cans: one at front-left desk edge, one back-center near the monitor; both visible across frames 1-10. Mapped to bottle as closest beverage-container label.
- desk ×1 — Single light-wood/white table filling the center of all frames 1-10.
- monitor ×1 — One Samsung LCD flat-panel monitor center-desk, all frames.
- keyboard ×1 — One dark keyboard in front of the monitor, all frames.
- cup ×1 — One white ceramic mug on the desk right of the mouse, all frames.
- plant ×1 — One potted green plant at the left desk edge, foliage visible all frames.
- lamp ×1 — Black round-headed object on a small tripod stand near the books, left of keyboard (frames 1-10); reads as a desk lamp/magnifier light. Uncertain but lamp-like.
- box ×1 — One cardboard box on the warehouse floor in the background behind the desk (frames 1-5). The small orange/yellow carton among the books is part of the book/binder cluster, not counted separately.
- floor ×1 — Concrete warehouse floor surrounding and beneath the desk, with painted alignment crosses/arrows, all frames.
- wall ×1 — Far-background warehouse structure: corrugated metal wall plus white panels/door area at the left/back (frames 1-7).
- _corr:_ box: reduced 2 -> 1. The background floor cardboard box is real; the small orange/yellow carton was double-counting items already inside the book/binder cluster, so removed.
- _corr:_ unknown object: increased 6 -> 7. Added the black-and-white checkerboard calibration target (clearly visible at right in frames 7-10); the draft omitted it but it is a distinct salient object.
- _corr:_ lamp: kept at 1 but flagged uncertain — the tripod-mounted black object is lamp-like (magnifier/clamp light) but could be an unknown object.
- _corr:_ Verified no chair, person, sofa, bed, sink, or trash can is visible; did not add any. Window/door in far background too ambiguous to count separately, folded into wall.
- _corr:_ Confirmed bottle=2 (two distinct Coke cans, not one re-counted across frames) and desk/monitor/keyboard/cup/plant/floor/wall all count 1.

## tum_rgbd_freiburg2_desk_with_person  (_high — all 10 frames are a near-static trajectory of one des_)
`{"desk": 1, "monitor": 1, "keyboard": 1, "plant": 2, "bottle": 2, "book": 1, "box": 1, "window": 1, "wall": 1, "floor": 1, "unknown object": 7}`  (19 objects)
- unknown object ×7 — Salient non-vocabulary instances: (1) brown teddy bear seated behind desk (all frames); (2) chrome/metallic sphere on small tripod stand (all frames); (3) black cylindrical disc/tape object on orange stand (all frames); (4) small red wheeled push-cart/toy on warehouse floor in right background (all frames); (5) white desk telephone on right edge of desk (all frames) — no vocab label; (6) computer mouse right of the keyboard (all frames) — no vocab label; (7) black camera tripod legs in left/center foreground (all frames) — no vocab label.
- plant ×2 — (1) Tall spiky yucca houseplant in dark blue pot, left foreground (all frames); (2) small yellow/red flowering plant behind the desk near the bear (all frames).
- bottle ×2 — Two upright cans mapped to nearest vocab 'bottle': (1) red Coca-Cola can standing on desk (all frames); (2) yellow aerosol/spray can beside the teddy bear (all frames).
- desk ×1 — Light-colored work desk filling foreground center in all 10 frames, holding monitor/keyboard/plant/cans/etc.
- monitor ×1 — Silver-bezel flat-panel LCD on right side of desk, visible every frame.
- keyboard ×1 — Computer keyboard in front of the monitor, all frames.
- book ×1 — Blue flat-lying hardcover/booklet on the desk left of center, all frames.
- box ×1 — White cardboard carton(s) standing behind the monitor; counted as one box cluster, all frames.
- window ×1 — Framed window in the upper-left background wall, visible all frames.
- wall ×1 — Corrugated dark-grey metal warehouse wall forming background, all frames.
- floor ×1 — Grey concrete warehouse floor around/behind the desk, all frames.
- _corr:_ Added unknown object: white desk telephone on right edge of desk (missed in-frame salient item, no vocab label).
- _corr:_ Added unknown object: computer mouse to right of keyboard (missed, no vocab label).
- _corr:_ Added unknown object: black camera tripod legs in foreground (missed, no vocab label).
- _corr:_ Raised 'unknown object' count from 4 to 7 to cover the three added instances (teddy, sphere, cylinder, cart, phone, mouse, tripod).
- _corr:_ Kept 'bottle' count 2 but clarified both are cans (Coca-Cola can + aerosol can) mapped to nearest vocab 'bottle' since 'can' is not in the vocabulary.
- _corr:_ Did NOT add 'person' despite scene name — no person is visible in any of the 10 frames.
- _corr:_ Verified all single surfaces/structures (desk, wall, floor, window) and single appliances (monitor, keyboard) remain count 1; no per-frame double counting introduced.

## tum_rgbd_freiburg2_coke  (_medium — central objects (can, table, chair, ladder, tripods_)
`{"bottle": 1, "table": 1, "floor": 1, "wall": 1, "chair": 1, "door": 1, "cabinet": 1, "box": 1, "monitor": 1, "unknown object": 4}`  (13 objects)
- unknown object ×4 — No vocab match: 1 aluminum A-frame step-ladder (center background, all frames); 2 black equipment tripods (center and right, all frames); 1 red fire extinguisher on the far-left wall (frames 6-10).
- bottle ×1 — Red Coca-Cola can on the table, central subject in all 10 frames. Mapped to 'bottle' (no 'can' in vocab).
- table ×1 — Single large light/cream table top the camera tracks along in every frame.
- floor ×1 — Tiled/concrete floor visible in background and bottom foreground (frames 1, 5, 9, 10).
- wall ×1 — White painted back/left walls behind the table, all frames.
- chair ×1 — One light wooden chair with thin metal legs, center-right background, visible in nearly every frame.
- door ×1 — White door with dark lever handle on the left background wall, clearest in frames 6-10.
- cabinet ×1 — One large beige standing panel/cabinet structure directly behind the ladder/chair in the center background, all frames. (Downcounted from draft's 2: the left white structure reads as wall/door, not a separate cabinet.)
- box ×1 — Cardboard-colored box on a small table/cart at the far right edge of the room in frames 1-2 (low-res, marginal).
- monitor ×1 — Dark flat screen-like object on the small table at far right in frames 1-2 (monitor/laptop; very low confidence due to distance and resolution).
- _corr:_ Downcounted cabinet from 2 to 1: the draft's 'white cabinet/locker at left in frames 1-3' is actually the wall/door region, not a distinct cabinet; only the beige standing panel behind the ladder/chair is a real cabinet-like structure.
- _corr:_ Kept bottle=1 (Coke can mapped to bottle, no 'can' in vocab) — confirmed single instance.
- _corr:_ Confirmed unknown object=4 (1 step-ladder, 2 tripods, 1 fire extinguisher) — none have a vocab label.
- _corr:_ Flagged monitor=1 as very low confidence: far-right edge object in frames 1-2 only, ambiguous at this resolution.
- _corr:_ Confirmed chair=1, door=1, table=1, wall=1, floor=1 as single instances/surfaces across the trajectory.

## tum_rgbd_freiburg2_dishes  (_medium - dishes/table/chair/door/structures are unambiguous;_)
`{"unknown object": 6, "cup": 1, "table": 1, "chair": 1, "desk": 1, "monitor": 1, "door": 1, "wall": 1, "floor": 1, "trash can": 1, "box": 1}`  (16 objects)
- unknown object ×6 — All frames: left blue cone bowl, center-back dark shallow bowl/plate, right dark bowl on the foreground table. Three distinct vessels, each seen across all 10 frames. | Camera tripod (black, center); aluminum step-ladder (left); large beige folding panel/partition (left-back). None are in-vocabulary; counted as three distinct salient items.
- cup ×1 — All frames: red straight-sided glass tumbler at center of the foreground table.
- table ×1 — All frames: the large light-wood foreground table holding the dishes.
- chair ×1 — Center-background wooden chair behind the table, visible in all frames.
- desk ×1 — Right-background metal-legged table/workbench with a laptop on it (frames 1-10).
- monitor ×1 — Open laptop on the right-background desk (closest vocab label); visible frames 1-10.
- door ×1 — White door with handle in center-background wall, visible in all frames.
- wall ×1 — White background wall of the room (large surface, count 1).
- floor ×1 — Gray floor visible in background under the structures.
- trash can ×1 — Dark cylindrical bin near the right-background desk, visible e.g. frames 6-8.
- box ×1 — Brown cardboard box/panel leaning at the left, visible in all frames.
- _corr:_ Draft 'bowl' had INVALID-PLACEHOLDER evidence and count 1; replaced with verified count 3 (left blue, center-back dark, right dark bowls).
- _corr:_ Added 'cup' 1: the central red glass tumbler was missed entirely.
- _corr:_ Added 'table' 1: the dominant foreground table was not in the draft.
- _corr:_ Added 'chair' 1: wooden chair in center-background.
- _corr:_ Added 'desk' 1: right-background workbench/table with laptop.
- _corr:_ Added 'monitor' 1: open laptop on right desk (closest vocab).
- _corr:_ Added 'door' 1: white door in center-background wall.
- _corr:_ Added 'wall' 1 and 'floor' 1: large background surfaces.
- _corr:_ Added 'trash can' 1: dark cylindrical bin by the right desk.
- _corr:_ Added 'box' 1: brown cardboard panel/box leaning at left.
- _corr:_ Added 'unknown object' 3: tripod, step-ladder, beige partition panel (out of vocab).

## tum_rgbd_freiburg2_flowerbouquet  (_medium — foreground objects and tripods/ladder/chair are cle_)
`{"plant": 1, "unknown object": 6, "table": 1, "desk": 1, "chair": 1, "monitor": 1, "wall": 1, "floor": 1, "door": 1, "window": 1, "picture": 1}`  (16 objects)
- unknown object ×6 — Grey ceramic jug/pitcher holding the bouquet (handle visible); foreground center all 10 frames. Not a cup/bottle in vocab. | Two black camera tripods in background (a thinner one and a heavier one with a black box/head); both clearly visible frames 7-10. | Aluminum A-frame stepladder in background left/center; clearest frames 3-10. | Orange plastic bucket on the floor at right edge near the desk; frames 1-2 (and faintly 4-5). | Large beige/tan board panel on wooden legs (easel/display board) in background left, distinct from the ladder; frames 5-10.
- plant ×1 — Central foreground flower bouquet (orange gerberas, yellow chrysanthemums, green foliage) in the jug; same bouquet in all 10 frames.
- table ×1 — Large light-wood foreground table the jug sits on; fills lower portion of every frame.
- desk ×1 — Grey-legged background work-table/desk assembly with laptop and items on top; frames 1-10.
- chair ×1 — Single beige seat chair with white tubular legs near the tripods; frames 1-7 clearest.
- monitor ×1 — Open silver laptop on the background desk (closest vocab term); visible across frames 1-6, 8-10.
- wall ×1 — White/off-white room walls forming the background in every frame (one continuous surface).
- floor ×1 — Grey concrete floor with a darker mat area, visible in background of all frames.
- door ×1 — Dark-handled door in the white back wall behind the tripods; frames 1-2, 4-6, 8-10.
- window ×1 — Bright overexposed daylight opening on the back-right wall; clearest frames 1-2, 4-5.
- picture ×1 — Small dark framed item mounted high on the back wall (picture/clock); top-center frames 1, 6, 10.
- _corr:_ Confirmed plant count 1 (one bouquet, same instance across frames).
- _corr:_ Confirmed jug -> unknown object count 1.
- _corr:_ Confirmed table count 1 and desk count 1 (background assembly kept as single desk, conservative).
- _corr:_ Confirmed chair count 1.
- _corr:_ Kept laptop -> monitor count 1 (closest vocab term).
- _corr:_ Confirmed two tripods -> unknown object count 2 (both visible frames 7-10).
- _corr:_ Confirmed stepladder -> unknown object count 1.
- _corr:_ ADDED orange bucket -> unknown object count 1 (missed in draft; floor right edge frames 1-2).
- _corr:_ ADDED beige board panel/easel -> unknown object count 1 (missed; background left frames 5-10, distinct from ladder).
- _corr:_ Confirmed wall, floor, door, window, picture all count 1.
- _corr:_ Left out marginal red cloth and white bottle on background desk (too ambiguous at resolution; conservative).

## tum_rgbd_freiburg2_metallic_sphere  (_medium — sphere/ball/tripod/plants/furniture are clear; drop_)
`{"table": 1, "desk": 1, "monitor": 1, "chair": 1, "plant": 2, "floor": 1, "wall": 1, "door": 1, "cabinet": 1, "picture": 2, "box": 1, "bottle": 1, "unknown object": 3}`  (17 objects)
- unknown object ×3 — (1) Central reflective metallic sphere on foreground table, every frame; (2) large blue inflatable/exercise ball at right-edge floor (frames 3-10); (3) camera tripod with splayed legs background-center (frames 1,3,4,5,8,9,10).
- plant ×2 — Tall potted yucca/dracaena center-background (all frames) plus a small red flowering potted plant on the desk (frames 1,3,4,5,6,7,9,10).
- picture ×2 — Two framed panels/notices mounted on dark back wall upper region, frames 1,3,8,9,10.
- table ×1 — Light-wood foreground table the sphere rests on; fills lower half of all 10 frames.
- desk ×1 — Dark-legged background work table holding monitor, plants, bottles; behind sphere in all frames (distinct from foreground table).
- monitor ×1 — Black flat-panel monitor on background desk, right of center, frames 1-10.
- chair ×1 — Wood/metal chair tucked under background desk; seat and splayed legs visible between desk legs, frames 1-10.
- floor ×1 — Grey concrete warehouse/lab floor spanning background of every frame.
- wall ×1 — Dark grey corrugated/paneled back wall behind desk and plant, all frames.
- door ×1 — Doorway/door panel on left side of room (wood + grey), frames 1,2,4,8,9,10.
- cabinet ×1 — White-and-blue fronted cabinet/locker units on far left, clearest in wide left views frames 8,10.
- box ×1 — Cardboard box on floor against back wall behind the plant, frames 1-10.
- bottle ×1 — Bottle/can containers on background desk beside red plant (red can + clear bottle), frames 1,3,4,5,7,10.
- _corr:_ Removed 'keyboard' (count 1): the dark elongated object right of the monitor is not confidently distinguishable from the cluster of miscellaneous dark equipment/boxes on the desk; cannot verify it is a keyboard.
- _corr:_ Kept 'desk' and 'table' as separate single instances (foreground light table vs background dark-legged work table) — correct disambiguation, no change.
- _corr:_ Confirmed plant count = 2 (large yucca + small red flowering desk plant), distinct instances.
- _corr:_ Confirmed picture count = 2 framed wall items.
- _corr:_ Confirmed unknown object count = 3 (metallic sphere, blue inflatable ball, tripod) — all distinct salient out-of-vocab instances, no double-counting across frames.
- _corr:_ All large surfaces (table, desk, floor, wall) held at count 1 per rules.

## tum_rgbd_freiburg2_360_hemisphere  (_medium — scene contents are clear, but window-vs-doorway-lig_)
`{"wall": 1, "floor": 1, "ceiling": 1, "table": 1, "chair": 2, "monitor": 1, "door": 2, "cabinet": 1, "bottle": 1, "bag": 1, "unknown object": 5}`  (17 objects)
- unknown object ×5 — (1) 3D laser scanner with red-orange top on black tripod, center/right, all frames; (2) second tripod-mounted scanner on the left, frames 5-10 (both visible together in frame 5); (3) tall yellow-and-black survey/light pole on folding tripod base in foreground, all frames; (4) small orange bucket on the floor center-right, frames 1-9; (5) large metal HVAC duct/pipe running across the upper wall, frames 1-6.
- chair ×2 — Tan/wooden chair beside the table (frames 1-7) and a second tan chair appearing bottom-left near the cabinet (frames 8-10).
- door ×2 — Closed white door with red fire-safety sign on the left wall, and a separate hinged white door at the center passage (open in most frames).
- wall ×1 — White-painted brick/concrete warehouse walls surrounding the room, all frames 1-10.
- floor ×1 — Bare concrete industrial floor across foreground, all frames.
- ceiling ×1 — High white ceiling/upper structure visible at top of frames 1-6 where the duct runs.
- table ×1 — One long grey-metal-legged work table holding a laptop, center, seen from rotating angles in all frames.
- monitor ×1 — Open laptop on the table with raised screen (frames 1-9); mapped to monitor as nearest vocab for the screen.
- cabinet ×1 — Tan/wooden cabinet standing against the far-left wall, visible frames 6-10.
- bottle ×1 — Clear plastic bottle(s) on the table near the laptop, visible frames 5-10.
- bag ×1 — Red cloth/bag item draped over the near edge of the table, frames 1-9.
- _corr:_ Added ceiling (count 1): high white ceiling visible at top of frames where the duct runs; was missed in draft.
- _corr:_ Removed window (count 1): the bright area is daylight through the open center doorway/passage, not a confirmable window pane in this room; ambiguous, dropped to stay conservative.
- _corr:_ Kept door at count 2 after re-checking the right-side panel — it appears to be the same center door seen open, not a third door.
- _corr:_ Kept chair at 2, table at 1, monitor(laptop) at 1, cabinet at 1, bottle at 1, bag at 1, unknown object at 5 — all independently confirmed.
- _corr:_ Confirmed unknown object=5: two separate tripod-mounted laser scanners, the yellow survey/light pole, the orange bucket, and the HVAC duct.

## tum_rgbd_freiburg2_large_no_loop  (_medium — heavy motion blur makes the tripod-count (2 vs 3) a_)
`{"wall": 1, "floor": 1, "ceiling": 1, "window": 1, "door": 1, "table": 1, "trash can": 1, "unknown object": 5}`  (12 objects)
- unknown object ×5 — Two surveying laser-scanner tripods (left + right, co-visible in frames 2,3,5,6,7; same two units re-framed as camera pans). One wall-mounted red fire extinguisher (frames 1,2,3,7,8,9,10). One small orange plastic bucket on the floor near the doorway (frames 7,8,9). One large green wall-mounted HVAC / air-handling unit with ducting (frames 1-8). Total 5. None in controlled vocabulary.
- wall ×1 — Large industrial wall, white upper / gray-painted lower, dominates frames 1-10. One structure.
- floor ×1 — Concrete floor visible in foreground of frames 7,8,9,10.
- ceiling ×1 — Wooden-beam ceiling visible at top of frames 4,5,6,7,8.
- window ×1 — Overexposed clerestory window high on the wall, frames 3,4,5,6,7,8. One opening, counted conservatively.
- door ×1 — Open white door panel / doorway into adjacent lit room on the left, frames 6,7,8,9.
- table ×1 — Dark table seen through the doorway in the adjacent room, frames 6,7,8.
- trash can ×1 — Gray rectangular bin standing on the floor against the wall, frames 7,8,9,10 (same instance).
- _corr:_ Kept wall/floor/ceiling/window/door/table/trash can as count 1 each — all single instances or structures; agree with draft.
- _corr:_ Downcounted tripods from 3 to 2: only a left and a right tripod are ever co-visible (frames 2,3,5,6,7); the alleged third is the same units re-framed as the camera pans, no clear independent third instance.
- _corr:_ Added the large green wall-mounted HVAC/air-handler unit (prominent in frames 1-8) which the draft omitted entirely — mapped to unknown object.
- _corr:_ Net unknown-object total unchanged at 5 (2 tripods + 1 extinguisher + 1 bucket + 1 HVAC unit), but composition corrected.
- _corr:_ Treated silver ductwork/pipes as building infrastructure (not a discrete countable object) to stay conservative; no person/monitor/keyboard/chair clearly visible.

## tum_rgbd_freiburg2_large_with_loop  (_medium - frames are dark/blurry; floor markers and the woode_)
`{"floor": 1, "wall": 1, "ceiling": 1, "window": 1, "door": 1, "plant": 1, "monitor": 1, "lamp": 1, "box": 1, "unknown object": 8}`  (17 objects)
- unknown object ×8 — Out-of-vocab items: (1) tripod with red scanner/total-station instrument on top (frames 1-10); (2) red fire extinguisher near the door (frames 6-10); (3) black-and-white checkerboard camera-calibration target leaning on the right wall (frames 6-10); (4) tall gray PVC/plastic pole/post in the foreground (frames 4-10); (5) tan wooden post in the foreground (frames 1-2), a separate object from the PVC pole; (6) long horizontal silver scale/rail bar mounted across the wall (frames 4-10); (7) metal step/extension ladder leaning against the far-left wall (frames 4-10), MISSED by the draft; (8) small colored marker/figurine survey targets on the floor (frame 1).
- floor ×1 — Single concrete/dirt warehouse floor in all 10 frames.
- wall ×1 — White warehouse walls plus white fabric/mesh partition panels surrounding the space, frames 1-10; one wall structure.
- ceiling ×1 — Industrial ceiling with steel roof trusses visible at top of frames 1-10.
- window ×1 — Bright clerestory window/openings near the ceiling upper-left, overexposed daylight strongest frames 1-5.
- door ×1 — Cream/beige metal door set in the wall on the right, same door visible frames 4-10.
- plant ×1 — Potted green leafy plant on floor at lower-left, frame 1 (faint far-left in frame 2).
- monitor ×1 — Dark flat computer monitor/screen sitting on the floor near the plant, frame 1.
- lamp ×1 — Fluorescent ceiling light fixture glowing upper-left, frames 4-10; one luminaire.
- box ×1 — Brown cardboard boxes/flat panels stacked at the right edge, frames 6-10; one cluster.
- _corr:_ Kept floor/wall/ceiling/window/door/plant/monitor/lamp/box at count 1 each - all confirmed single instances.
- _corr:_ MISSED: added metal step/extension ladder leaning on the far-left wall (frames 4-10) - a distinct out-of-vocab instance not in the draft.
- _corr:_ MISSED: added the long horizontal silver scale/calibration rail bar mounted across the wall (frames 4-10) - salient and separate from the tripod.
- _corr:_ UNDERCOUNT FIX: split the draft's lumped pole entry - the tan wooden post (frames 1-2) and the gray PVC pole (frames 4-10) are separate physical objects at different positions, counted as 2 not 1.
- _corr:_ UNDERCOUNT FIX: floor marker/figurine survey targets (frame 1) counted as a distinct unknown instance rather than folded into the pole entry.
- _corr:_ Raised 'unknown object' count from 4 to 8 to reflect distinct out-of-vocab instances (tripod, extinguisher, checkerboard, PVC pole, wooden post, scale bar, ladder, floor markers).
- _corr:_ No hallucinations removed - all draft in-vocab labels verified present.

## tum_rgbd_freiburg3_long_office_household_validation  (_medium - object inventory is clear, but exact bottle count (_)
`{"desk": 1, "box": 1, "chair": 2, "wall": 1, "floor": 1, "bottle": 6, "book": 2, "cup": 2, "bag": 1, "unknown object": 6}`  (23 objects)
- bottle ×6 — On box top: two Vittel water bottles + one green soda bottle (all frames). On desk by wall: teal glass bottle, clear plastic water bottle, dark brown bottle = 6 distinct bottles. Draft undercounted at 4.
- unknown object ×6 — Globe (blue Earth sphere on box, all frames); large yellow foam die (all frames); red/white toy airplane (all frames); orange/red plastic peeler tool (all frames); orange-handled scissors on desk (all frames); yellow pencil on desk (all frames). None in vocabulary.
- chair ×2 — Maroon padded chair bottom-left (frames 1,8,9,10) and wooden-seat swivel chair bottom-right (all frames).
- book ×2 — Purple 'Katalog' O'Reilly book lying flat, and a striped book/notebook standing upright behind it; all frames.
- cup ×2 — White coffee cup on a saucer at right (all frames) and a small yogurt-style cup/container near the desk bottles.
- desk ×1 — White desk/table surface (corner of two abutting tables) holding all items; all 10 frames. One surface.
- box ×1 — White freestanding box/divider sitting on the desk with bottles and globe on top; all frames. No doors visible -> 'box' fits better than cabinet.
- wall ×1 — Tan/brown back wall behind the desk in all frames.
- floor ×1 — Gray tiled floor under the desk in all frames.
- bag ×1 — Blue/white snack/chips bag standing at far-right back of desk against the wall; all frames.
- _corr:_ Reclassified 'cabinet' -> 'box': freestanding box on desk with no doors; 'box' is the correct in-vocab label.
- _corr:_ Increased bottle count 4 -> 6: clearly 3 on box top (2 Vittel + 1 green) plus 3 distinct bottles on the desk by the wall (teal glass, clear plastic, brown).
- _corr:_ Removed the 'picture' entry: it was self-negating (mapped a globe then said NOT counted); the globe is already in unknown object.
- _corr:_ Increased unknown object 4 -> 6: added orange-handled scissors and the yellow pencil, both salient and in all frames, not in vocabulary.
- _corr:_ Kept chair=2, book=2, cup=2, desk/wall/floor/bag=1 as correctly counted (single instances seen across the trajectory).

## tum_rgbd_freiburg3_cabinet  (_medium - box vs cabinet is the only real judgment call; no c_)
`{"box": 1, "floor": 1, "person": 1, "unknown object": 1}`  (4 objects)
- box ×1 — The dominant object in all 10 frames: a large smooth purple/blue rectangular prism on the floor. NO visible doors, handles, drawers, or seams, so physically it reads as a plain closed box, not a cabinet. Same instance orbited across all frames -> count 1.
- floor ×1 — Light off-white/beige flat floor under the box, visible in every frame. Single surface -> count 1.
- person ×1 — Human lower legs/feet in jeans with light sneakers at the top-left edge in frames 1, 2, 3, 7, 8. Only feet visible; same person -> count 1.
- unknown object ×1 — Thin yellow/beige cable(s)/cord(s) trailing across the floor in frames 2-10. Cable/cord not in vocabulary; persistent feature counted once.
- _corr:_ Remapped 'cabinet' -> 'box': the visible object is a featureless smooth rectangular prism with no doors/handles/drawers/seams; despite the sequence name, what is physically observable is a plain box. (Vocab has both labels; chose the one matching visible features.)
- _corr:_ Kept floor count 1 (single surface across all frames).
- _corr:_ Kept person count 1 (same legs/feet seen in frames 1,2,3,7,8, not multiplied per frame).
- _corr:_ Kept 'unknown object' count 1 for the cord/cable set (same cords across frames, counted once).
- _corr:_ Did NOT add the faint thin white poles/tubing in the far background top-left (frames 1,3-7): too small/ambiguous/distant to map confidently to any vocab label.

## tum_rgbd_freiburg3_large_cabinet  (_medium — clear scene and counts; main ambiguity is cabinet-v_)
`{"cabinet": 1, "door": 2, "wall": 1, "floor": 1, "curtain": 1, "desk": 1, "chair": 1, "box": 1, "unknown object": 4}`  (13 objects)
- unknown object ×4 — Camera tripod background-left (frames 1-9); red wall-mounted fire extinguisher background (frames 2-9); white whiteboard/partition panel background-left (frames 1-7); power strip on right wall (frames 8-10). None in vocabulary.
- door ×2 — Right-wall white door with orange sign + handle (frames 1-10); a second white door appears in background-left (frames 6-10). Two distinct doors.
- cabinet ×1 — Tall white open-frame shelving unit with dark shelves, central subject in all 10 frames. Open (no doors) so 'shelf' is arguably more apt, but kept as cabinet. One instance orbited by camera.
- wall ×1 — White room walls surrounding the scene in every frame.
- floor ×1 — Light gray lab floor across all frames with faint tape markings.
- curtain ×1 — Dark mesh/netting hanging on the right wall, frames 5-10.
- desk ×1 — Background-left lab table(s) with light tops on metal legs (frames 1-8). Counted as one conservatively.
- chair ×1 — Orange/wood swivel office chair on castors at background-left desk, frames 1-8.
- box ×1 — Tan/brown cardboard box on the floor at background-left near the tables (frames 1-3,5-8). In-vocab; missed by draft.
- _corr:_ Added 'box' count 1: tan cardboard box on floor at background-left, in-vocab and missed by draft.
- _corr:_ Verified door count 2: confirmed both the right-wall door and the second background-left door are distinct.
- _corr:_ Verified unknown object count 4 (tripod, fire extinguisher, whiteboard/partition, power strip) — all real and out-of-vocab; no hallucinations.
- _corr:_ Kept cabinet count 1 but noted the unit is an open shelving frame, so 'shelf' is the more accurate vocab map.
- _corr:_ Confirmed wall/floor/curtain/desk/chair all count 1; no over-counting of single instances across frames.

## tum_rgbd_freiburg3_teddy  (_medium — core objects confidently verified; door count (2) a_)
`{"unknown object": 4, "box": 2, "person": 1, "chair": 1, "desk": 1, "cabinet": 1, "door": 2, "curtain": 1, "wall": 1, "floor": 1}`  (15 objects)
- unknown object ×4 — (1) Large brown plush teddy bear in yellow/blue-striped shirt, central object, all 10 frames. (2) Black camera tripod, left background frames 1-3. (3) Red wall-mounted fire extinguisher, background frames 1-3. (4) Thin cable/wire on the floor across frames 1,2,5,9,10. None in vocab.
- box ×2 — (1) White rectangular pedestal the teddy sits on, all 10 frames. (2) Tan cardboard box on floor in left background frames 1-3.
- door ×2 — Two distinct white doors visible together in the room background: a left door (with handle) and a right door, clearly co-visible in frames 8,9,10.
- person ×1 — Partial person at left edge of frame 1: dark blue shirt, camo shorts, sneaker.
- chair ×1 — Wheeled office chair near left edge behind the person, frames 1-2.
- desk ×1 — Small desk/table surface behind the person on the left, frames 1-2.
- cabinet ×1 — Gray mobile rolling drawer cabinet on the right side, frames 9-10.
- curtain ×1 — Tall narrow dark/black hanging drape on the right-center background, frames 5,8,9,10 (vertical fabric hanging from above).
- wall ×1 — White room walls in the background of all 10 frames.
- floor ×1 — Large gray floor surface filling the lower portion of all 10 frames.
- _corr:_ Added curtain (count 1): tall dark hanging drape on right-center background in frames 5,8,9,10 — missed in draft.
- _corr:_ Changed door count 1 -> 2: a left door (with handle) and a right door are co-visible in frames 8-10, so they are distinct physical doors.
- _corr:_ Kept unknown object at 4 (teddy, tripod, fire extinguisher, floor cable) — all independently confirmed.
- _corr:_ Kept box at 2 (white pedestal + tan cardboard box) — confirmed.
- _corr:_ Kept person/chair/desk/cabinet at 1 each — all confirmed as single instances; no over-counting found.
- _corr:_ Verified wall and floor are single large surfaces (count 1).

## tum_rgbd_freiburg3_sitting_static  (_high — static scene, single desk, objects consistent and cle_)
`{"person": 2, "chair": 2, "desk": 1, "monitor": 2, "keyboard": 2, "bottle": 1, "book": 1, "picture": 1, "wall": 1, "floor": 1, "ceiling": 1, "unknown object": 2}`  (17 objects)
- person ×2 — Two men face each other across the desk in all frames: left in black T-shirt/camo shorts, right in green-white plaid shirt/grey shorts.
- chair ×2 — Left man on a black swivel office chair with casters; right man on a wooden cantilever/sled chair. Both visible frames 1-10.
- monitor ×2 — Silver-bezel LCD on the left and larger black widescreen LCD on the right, both on the desk (all frames).
- keyboard ×2 — One keyboard in front of each monitor on the desk (e.g. frames 1, 5, 8).
- unknown object ×2 — (1) Computer mouse on the desk beside the left keyboard (frames 1-10) - no 'mouse' in vocab. (2) Yellow rubber duck toy on the desk center (frames 1, 3, 5, 8).
- desk ×1 — One long light-topped office desk with metal legs spanning the scene, holding monitors and keyboards (all frames).
- bottle ×1 — Green translucent plastic drink bottle on the right side of the desk near the black monitor (frames 3-10).
- book ×1 — A stack of books/binders (blue and white covers) on the desk center, counted as one stack (frames 1-10).
- picture ×1 — Printed poster/papers pinned to the brown cubicle partition (center sheet with text/logos) plus a printed sheet on the left white panel.
- wall ×1 — Brown fabric/cardboard cubicle partition (with white panel dividers above) behind the desk, dividing the workspace (all frames).
- floor ×1 — Gray smooth office floor under the chairs and feet (all frames).
- ceiling ×1 — Industrial ceiling with exposed metal pipes, ducts and roof trusses in the upper background (all frames).
- _corr:_ Verified all draft counts independently across 10 frames; no instance was over-counted by re-counting the same object in multiple frames.
- _corr:_ Kept person=2, chair=2 (distinct office swivel chair vs wooden cantilever chair), monitor=2, keyboard=2 — all confirmed.
- _corr:_ Kept desk/wall/floor/ceiling each =1 as single large structures (partition treated as 'wall').
- _corr:_ Confirmed bottle=1 (green bottle, right side) and book=1 (single binder/book stack).
- _corr:_ Confirmed unknown object=2: mouse and rubber duck (both salient, not in vocabulary).
- _corr:_ Considered adding 'window' for the bright far-left glazing but rejected as too ambiguous (could be bright background/doorway) — conservative.
- _corr:_ No hallucinations found; no confident in-vocab misses to add.

## tum_rgbd_freiburg3_sitting_xyz  (_medium — frames are consistent and most objects are clear; c_)
`{"person": 2, "desk": 1, "monitor": 2, "keyboard": 2, "chair": 2, "book": 1, "bottle": 1, "lamp": 1, "cabinet": 1, "picture": 2, "wall": 1, "window": 1, "floor": 1, "ceiling": 1, "box": 1, "unknown object": 2}`  (22 objects)
- person ×2 — Two men seated facing each other across the desk in all 10 frames: left man in dark T-shirt with beard, right man in green plaid shirt with glasses.
- monitor ×2 — Silver-framed LCD on the left and a black widescreen LCD on the right, all frames.
- keyboard ×2 — Two keyboards, one in front of each monitor (frames 1-10).
- chair ×2 — Light wooden chair back behind left man; right man's chair frame visible (frames 1, 8, 9, 10).
- picture ×2 — Framed colorful picture on the left partition and a printed flyer/poster on the center partition, all frames.
- unknown object ×2 — Orange/red rubber-duck-like toy figure on the center of the desk (all frames), and a computer mouse on the desk beside the left keyboard (frames 1-10) — mouse is out-of-vocab.
- desk ×1 — One long continuous white desktop spanning the scene holding both monitors/keyboards, all frames.
- book ×1 — A stack of books/binders on the center of the desk, all frames; counted as one cluster.
- bottle ×1 — Clear/greenish plastic drink bottle standing on the right side of the desk, frames 1-10.
- lamp ×1 — Orange clamp/desk lamp mounted on the right-side cabinet, clearly visible frames 6-10.
- cabinet ×1 — Cabinet/drawer pedestal unit on the right behind the right monitor (frames 3-10).
- wall ×1 — Brown cubicle partition panels behind the desk forming the back enclosure, all frames.
- window ×1 — Bright daylight window openings on the left side of the scene, all frames.
- floor ×1 — Concrete office floor visible in the lower portion of frames 1, 4, 6, 9.
- ceiling ×1 — Industrial warehouse roof with wooden trusses and overhead metal scaffolding (all frames); scaffolding is part of building structure, not separately counted.
- box ×1 — Small blue box/container sitting next to the book stack on the desk (frames 4-10); 'box' is in-vocab so reclassified from unknown object.
- _corr:_ Added 'unknown object' for the computer mouse on the desk by the left keyboard (visible all frames) — was MISSED.
- _corr:_ Reclassified the small blue box from 'unknown object' to 'box' (in-vocab), so box=1.
- _corr:_ Net unknown object count stays at 2 (orange duck toy + mouse) after removing the blue box and adding the mouse.
- _corr:_ Clarified ceiling evidence: overhead scaffolding/trusses are part of building structure, not a separate countable instance.
- _corr:_ Confirmed all other counts (person 2, desk 1, monitor 2, keyboard 2, chair 2, book 1, bottle 1, lamp 1, cabinet 1, picture 2, wall 1, window 1, floor 1) — no hallucinations or miscounts found.

## tum_rgbd_freiburg3_sitting_halfsphere  (_medium - all major objects confirmed across frames; book=2 (_)
`{"person": 2, "chair": 2, "desk": 1, "cabinet": 1, "monitor": 2, "keyboard": 2, "book": 2, "bottle": 1, "picture": 1, "bag": 1, "wall": 1, "floor": 1, "unknown object": 3}`  (20 objects)
- unknown object ×3 — (1) Computer mouse on the desk at far left near the silver monitor (frames 1-10) - 'mouse' not in vocab. (2) Yellow rubber duck toy on top of the book stack (most frames). (3) Metal scaffolding/ladder tower in the warehouse background at far right (frames 1-4).
- person ×2 — Main seated man in green/white plaid shirt and glasses in all 10 frames. Second person (camouflage/cargo-short leg, arm, sandaled foot) at lower-left edge in frames 1,4,5,7,9,10 on the wheeled chair.
- chair ×2 — Man's pale blond plywood cantilever chair (curved seat/back on bent metal legs) in all frames. Second dark office chair with castor wheels at lower-left (frames 1,9,10).
- monitor ×2 — Central black flat-panel monitor (all frames) and a second silver/light-framed monitor at far left of desk (frames 1-5).
- keyboard ×2 — Black keyboard in front of central monitor (all frames) and a second keyboard at far-left near the silver monitor (frames 1-10).
- book ×2 — A single stack of books on the desk with two clearly distinct volumes (red/orange spine atop a blue/white spine), frames 1-10. Counting the two visibly distinct volumes.
- desk ×1 — One long white-topped office desk the man sits at, with cardboard partition along its back edge; one continuous surface across all frames.
- cabinet ×1 — Dark charcoal cabinet/credenza at the right end of the desk, frames 3-10.
- bottle ×1 — Small green/clear plastic drink bottle on the desk just right of the central monitor (frames 1,2,3,5,8,9,10).
- picture ×1 — Printed yellow poster/flyer pinned to the cardboard partition behind the silver monitor (frames 1-5).
- bag ×1 — White plastic bag at the man's lower back / hanging by the chair near the orange container under it (frames 1-7). 'bag' is in vocab, so mapped here rather than unknown.
- wall ×1 — Brown cardboard cubicle partition plus white wall/divider panels forming the backdrop; one continuous structure across all frames.
- floor ×1 — Gray/light tiled office floor in the foreground of all frames.
- _corr:_ Re-mapped the white plastic bag from 'unknown object' to 'bag' (bag is in the controlled vocabulary).
- _corr:_ Decremented unknown object from 4 to 3 (mouse, rubber duck, scaffolding) after moving the bag out.
- _corr:_ Kept book=2 but clarified it is a single physical stack with two visibly distinct volumes, not two separate piles.
- _corr:_ Verified person=2 and chair=2: second person and dark wheeled chair confirmed at lower-left in several frames.
- _corr:_ Verified monitor=2 and keyboard=2: distinct far-left silver monitor and second keyboard confirmed.
- _corr:_ Did not add the orange container under the chair as a separate object; it is ambiguous and folded with the bag region to stay conservative.

## tum_rgbd_freiburg3_walking_xyz  (_medium — core inventory (people, chairs, monitors, desk, boo_)
`{"person": 2, "chair": 2, "desk": 1, "monitor": 2, "keyboard": 2, "book": 1, "bottle": 1, "lamp": 1, "cabinet": 1, "trash can": 1, "picture": 1, "floor": 1, "ceiling": 1, "wall": 1, "window": 1, "unknown object": 4}`  (23 objects)
- unknown object ×4 — (1) Orange/yellow rubber toy duck on the desk near center (frames 1-10); (2) brown teddy bear plush on floor in front of the side cabinet (frames 3-10); (3) black computer mouse on the desk left of the keyboard (frames 1-3,7,9); (4) free-standing brown/white cubicle partition divider behind the desk (all frames). None are in the vocabulary.
- person ×2 — Seated man in black T-shirt and cargo shorts (left, all frames); standing man in green plaid shirt and grey shorts (right, all frames). Two distinct people.
- chair ×2 — Black office swivel chair the left man sits on (frames 1-4); empty wooden/plywood stacking chair in foreground center (frames 1-10). Two distinct chairs.
- monitor ×2 — Two flat-panel displays: smaller silver 4:3 monitor on the left (frames 1-4) and a larger black widescreen monitor center/right (all frames).
- keyboard ×2 — Two black keyboards on the desk in frames 1-2 (one per workstation); central keyboard persists in later frames.
- desk ×1 — One long white-topped workstation desk with metal legs holding monitors/keyboards (all frames).
- book ×1 — Stack of books with colored/blue covers lying flat on the desk near center (frames 2-10). One stack.
- bottle ×1 — Green plastic bottle standing on the desk right of the central monitor (frames 1-10).
- lamp ×1 — Orange/red articulated desk lamp on the side cabinet at right (clearly visible frames 7-10).
- cabinet ×1 — Low grey/white pedestal cabinet at the right end of the desk; teddy bear sits in front of it (frames 3-10).
- trash can ×1 — Round bin with pink/orange plastic liner on the floor by the wooden chair (frames 5-10).
- picture ×1 — Paper poster/notice pinned to the brown partition behind the desk (frames 1-10), mapped to 'picture' as a wall-mounted printed sheet.
- floor ×1 — Grey polished concrete/epoxy floor of the hall, visible throughout.
- ceiling ×1 — Industrial hall roof with exposed metal trusses, beams and skylights across the top of all frames.
- wall ×1 — Light grey/corrugated far wall of the hall behind the partitions (frames 1-3,5-7,10).
- window ×1 — Bright glazed window/opening on the far left of the hall (frames 1-4), and bright glazed openings at right.
- _corr:_ Removed 'shelf' (count 1): the brown/white cubicle partition is a free-standing room divider, not a shelf (no horizontal storage surface visible). Reclassified it as 'unknown object'.
- _corr:_ Merged the separate 'mouse' line into 'unknown object' (the draft already noted mouse is out-of-vocab but left it as its own labeled entry).
- _corr:_ Increased 'unknown object' from 2 to 4: duck + teddy bear + mouse + cubicle partition.
- _corr:_ Added 'window' (count 1): bright glazed hall opening visible on the far left of frames 1-4.
- _corr:_ Verified monitor=2 and keyboard=2: frames 1-2 clearly show two distinct workstation monitors and two keyboards.
- _corr:_ Kept all large-structure counts at 1 (desk, floor, ceiling, wall) and person/chair at 2 each as physically distinct instances.

## tum_rgbd_freiburg3_walking_static  (_high — draft was accurate; independent review of all 10 fram_)
`{"person": 2, "chair": 3, "desk": 1, "monitor": 2, "keyboard": 2, "book": 1, "bottle": 1, "cup": 1, "cabinet": 1, "shelf": 1, "picture": 1, "wall": 1, "floor": 1, "ceiling": 1, "unknown object": 2}`  (21 objects)
- chair ×3 — Empty tan wooden-back chair far left (frames 1-10); black pedestal swivel saddle-stool the left man uses (all frames); tan wooden chair the right man sits on (all frames).
- person ×2 — Two men in all 10 frames: left man in dark T-shirt and camo shorts (seated on stool frames 1-7, standing frames 8-10), right man in green plaid shirt seated at desk.
- monitor ×2 — Left silver-bezel LCD and right larger black flat-panel, both on the desk in all frames.
- keyboard ×2 — One keyboard in front of each monitor (left and right) on the desk, frames 1-10.
- unknown object ×2 — Black computer mouse beside the left keyboard (frames 1-10); yellow/orange rubber-duck-like toy on the desk center (frames 1-10). Neither label is in the vocabulary.
- desk ×1 — One long shared white office desk spanning the center of every frame, holding both workstations.
- book ×1 — Stack of books at center of the desk, visible frames 1-10 (counted once as a stack).
- bottle ×1 — Green/clear plastic drink bottle standing on the right portion of the desk in all frames.
- cup ×1 — Small blue cup/container on the desk near center, visible across frames.
- cabinet ×1 — White cabinet/cupboard unit at desk-right behind the seated right man (frames 1-10).
- shelf ×1 — Shelving/rack unit in the far-right background behind the partition (frames 1-3,7-10).
- picture ×1 — Framed colored poster on the left partition panel plus paper notices pinned on the partition (frames 1-10).
- wall ×1 — Beige cubicle partition wall (panel system) running behind the desk across all frames.
- floor ×1 — Continuous gray office floor in the foreground of all frames.
- ceiling ×1 — Industrial open ceiling with metal ducts, pipes and trusses across the top of all frames.
- _corr:_ No changes to person (2): two men confirmed across all frames, left one standing in frames 8-10.
- _corr:_ No changes to chair (3): confirmed three distinct seats — empty wooden chair, swivel stool, right man's wooden chair.
- _corr:_ No changes to monitor/keyboard (2 each): one of each per workstation, confirmed.
- _corr:_ No changes to desk/wall/floor/ceiling (1 each): single large surfaces, per counting rule.
- _corr:_ Kept cup (1): small blue desk object is ambiguous but cup is a reasonable conservative mapping.
- _corr:_ Kept shelf (1) and cabinet (1): both background storage units confirmed as distinct.
- _corr:_ Verified unknown object (2): mouse and rubber-duck toy are genuinely out-of-vocab; count and mapping correct.
- _corr:_ Considered but did NOT add 'window' (far-left bright glare too washed out to confirm) or 'door' (far-right dark opening not clearly resolvable) — conservative.

