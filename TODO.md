# TODO.md - Outstanding Tasks for Dungeon Port

*Audited against `skeins/` regression suite (`tools/skein.py diff`):
674/674 nodes match. Completed = exercised by a passing skein
(`default.skein` counts). The suite is currently clean, including the
former bat/balloon regressions (see bottom).*

## 1. Object Action Routines (Missing)

- ~~**MIRROR-MIRROR** – `src/rooms/mirror.dg`~~ ✅ `default.skein` `touch mirror` (×2, swaps Mirror Room 1↔2)
- ~~**ROBBER-FUNCTION** – `src/rooms/thief.dg`~~ ✅ `default.skein` (3 encounters, `kill thief with knife` → melee → thief dies, leaves stilletto, sword glow ends). All interaction branches ported and hand-verified with `tools/skein.py play --seed <n>`: OUT!!/IN!! knockout cycle (unconscious description, stilletto hidden in `#hidden-treasures`, chalice guard lifted, "His booty remains." on death, revive after a 2-tick timer), GIVE/THROW-to-thief ("places the X in his bag and thanks you politely", revive-on-give while unconscious, brick-with-lit-fuse refusal), THROW knife (10% frightened flee + bag contents drop / 90% angered), TAKE thief ("Once you got him..."), and the FIGHT-branch retrieve/slip-away now actually reachable (a leftover unit fact `(#thief wields #stilletto)` used to shadow the wields rules). Note: the old `give egg to thief` test was a red herring — the jewel egg does not exist in the '77 game; use `give chalice to thief`. Still open: the ROBBER daemon's wandering/robbing branches (see ROBBER daemon entry in §5)
- ~~**BALLOON** – `src/rooms/volcano.dg`~~ ✅ `edges/balloon.skein`, `deaths/volcano.skein`, `edges/gnome-*.skein` (inflate, ascend, drive, land, disembark, float away, rim death)
- **TUBE-FUNCTION** – `src/rooms/volcano.dg` (tube itself done: ✅ `edges/blue-leak.skein` `open tube` → viscous material)
- **WIRE-FUNCTION** – `src/rooms/volcano.dg` (untested: anchoring balloon to hook)
- ~~**CYCLOPS** – `src/rooms/cyclops.dg`~~ ✅ `edges/cyclops-feeding.skein`, `edges/cyclops-wake.skein`, `deaths/cyclops.skein`
- ~~**CHALICE** – `src/rooms/treasure-room`~~ ✅ `default.skein` `get chalice` blocked mid-fight, takable after thief dies
- **HEAD-FUNCTION** – `src/rooms/cyclops.dg` (untested; `deaths/tomb.skein` only covers attack-tomb)
- ~~**BODY-FUNCTION** – `src/rooms/hades.dg`~~ ✅ `deaths/bodies.skein` (attack → death), `edges/bodies-take.skein` (force refuses take)
- ~~**CYCLOPS-ROOM** – `src/77act1.mud`~~ ✅ `deaths/cyclops.skein` (full taunt ladder)
- **COKE-BOTTLES** – `src/rooms/hades.dg` (untested)
- ~~**GHOST-FUNCTION** – `src/rooms/hades.dg`~~ ✅ `edges/ghost-curse.skein` (attack bones → curse, valuables banished)
- **DDOOR-FUNCTION** – `src/rooms/autogen.dg` (untested)
- **FLY-ME** – `src/rooms/autogen.dg` (has skeins but they currently FAIL — see Known regressions)
- **STICK-FUNCTION** – `src/rooms/autogen.dg` (untested)
- ~~**DUMBWAITER** – `src/rooms/coalmine.dg`~~ ✅ `default.skein` (`lower basket`/`raise basket` with diamond, torch, screwdriver)
- ~~**NO-OBJS** – `src/rooms/coalmine.dg`, etc.~~ ✅ `default.skein` ("You cannot fit through this passage with that load.")
- ~~**MACHINE-ROOM** – `src/rooms/coalmine.dg`~~ ✅ `default.skein` (`turn switch`, `open lid`)
- ~~**MSWITCH-FUNCTION** – `src/rooms/coalmine.dg`~~ ✅ `default.skein` (`turn switch`)
- ~~**FLASK-FUNCTION** – `src/rooms/tearoom.dg`~~ ✅ `default.skein` `read blue through flask` ("The icing, now visible, says 'Enlarge'.")
- ~~**EATME-FUNCTION** – `src/rooms/tearoom.dg`~~ ✅ `default.skein` `eat eat me cake`; `deaths/cake-blue.skein`, `deaths/cake-orange.skein`
- ~~**CAKE-FUNCTION** – `src/rooms/tearoom.dg`~~ ✅ `default.skein` `eat blue cake`; `edges/cake-blue-posts.skein`
- **LEAD-GATE** – `src/rooms/dam.dg` (untested)
- ~~**MATCH-FUNCTION** – `src/rooms/dam.dg`~~ ✅ `edges/dam-reading.skein` (read), match count/burnout in `deaths/brick.skein`, `edges/balloon.skein` ("The match has gone out")
- ~~**BOLT-FUNCTION** – `src/rooms/dam.dg`~~ ✅ `default.skein` `turn bolt` + `wrench` → sluice gates open
- ~~**LEAK-FUNCTION** – `src/rooms/dam.dg`~~ ✅ `edges/blue-leak.skein` (button, plug with putty), `deaths/leak.skein` (drowning ladder), `edges/leak-munged.skein`
- ~~**LEDGE-FUNCTION** – `src/rooms/volcano.dg`~~ ✅ `edges/balloon.skein` (land on narrow ledge), `edges/gnome-treasure.skein`, `edges/gnome-departs.skein`
- ~~**CYCLE-PRIMARY** – `src/77act1.mud`~~ ✅ `deaths/cyclops.skein` (full taunt escalation)
- ~~**CYCLOPS-FLAG** – `src/rooms/cyclops.dg`~~ ✅ `edges/cyclops-*.skein` (asleep opens stairs, wake blocks)
- **MAGIC-FLAG** – `src/rooms/cyclops.dg` (untested)
- ~~**EMPTY-HANDED** – `src/rooms/coalmine.dg`, `lower-shaft`, etc.~~ ✅ `default.skein` (load refusal enforced)

## 2. Room Action Routines (Missing)

- ~~**DAM-ROOM** – `src/rooms/dam.dg`~~ ✅ `default.skein` (bolt/wrench → gates open, reservoir drained, "go to reservoir")
- ~~**MAINT-ROOM** – `src/rooms/dam.dg`~~ ✅ `edges/maintenance-buttons.skein` (red/yellow/brown), `edges/blue-leak.skein` (blue), `default.skein` `push yellow`
- ~~**MACHINE-ROOM** – `src/rooms/machine.dg`~~ ✅ `default.skein`
- **LLD1-ROOM** – `src/rooms/hades.dg` (untested — gate force not exercised)
- **LLD2-ROOM** – `src/rooms/hades.dg` (only teleport-in coverage via `deaths/bodies.skein`)
- ~~**TREASURE-ROOM** – `src/77act1.mud`~~ ✅ `edges/cyclops-feeding.skein` (scream of anguish, thief defends), `default.skein` (chalice guard)
- **BOOM-ROOM** – `src/rooms/coalmine.dg` (untested)
- **TIME** – `src/77act1.mud` (mine-entrance) (untested)
- ~~**NO-OBJS**~~ ✅ see §1
- ~~**CYCLE-PRIMARY**~~ ✅ see §1
- ~~**CYCLOPS-FLAG**~~ ✅ see §1
- **MAGIC-FLAG** – `src/77act1.mud` (untested)
- **FROBOZZ** – `src/77act1.mud` (autogen/magnet room) (untested)
- ~~**RIDDLE-FLAG** – `src/77act1.mud`~~ ✅ `default.skein` (`say well` → clap of thunder, door opens)

## 3. Flag & Conditional Logic

- ~~`CYCLOPS-FLAG` – Cyclops presence/state~~ ✅ `edges/cyclops-*.skein`
- `MAGIC-FLAG` – Magic item availability (untested)
- ~~`EMPTY-HANDED` – Weight limit enforcement (multiple rooms)~~ ✅ `default.skein`
- `DOME-FLAG` – Volcano danger state (untested)
- `LLD-FLAG` – Hades room lock state (untested)
- ~~`RIDDLE-FLAG` – Riddle puzzle activation~~ ✅ `default.skein`
- `FROBOZZ` – Frobozz flag (autogen) (untested)

## 4. Critical Bugs / Quality Issues

- ~~**Combat continues after death** – `src/core/melee.dg`~~ ✅ `deaths/troll.skein` (post-death turns produce only menu junk, no combat) — stale `%% TODO` comment in source remains
- **Performance bottleneck** – `src/core/melee.dg` (combat table lookup)
- **Weapon management** – `src/core/melee.dg` (unwield, tracking) (untested)
- **Darkness handling** – partially covered: `deaths/grue.skein`, `edges/lamp-dimming.skein`, `(inherently dark *)` on cave rooms; full enforcement unverified
- ~~**Thief logic** – missing `ROBBER-FUNCTION` and related mechanics~~ ✅ `default.skein` + `edges/cyclops-feeding.skein`; full branch coverage noted in §1 (the old "give egg to thief" grammar-gap note was a red herring: there is no egg in the '77 game)
- ~~**Cyclops AI** – cyclops behavior not fully implemented~~ ✅ `edges/cyclops-*.skein`, `deaths/cyclops.skein`
- ~~**Balloon physics** – launch, ascent, descent, and landing not functional~~ ✅ `edges/balloon.skein` + `deaths/volcano.skein` (one node drifting: formatting + 0→10 score at death — bless candidate)
- ~~**Machine room** – machine controls and effects incomplete~~ ✅ `default.skein`
- **Score/point system** – per-object/per-room awards work throughout skeins; final endgame scoring (trophy-case sum, `house.dg`) still TODO and untested

## 5. Feature Gaps

- **Darkness system** – partially done (grue death, lamp dimming tested); see §4
- ~~**Thief mechanics** – robbing, item movement, and AI missing~~ ✅ `default.skein`, `edges/cyclops-feeding.skein` for the co-located/defend-lair cases; the ROBBER daemon's **wandering** branches are still open:
  - **ROBBER daemon wandering** – `src/rooms/thief.dg` (77act1.mud:1284): the thief never roams; he should move between rooms each tick, rob rooms ("A seedy-looking individual... abstracted all valuables..."), rob the player ("You suddenly notice that the X vanished"), drop junk ("The robber, rummaging through his bag, dropped a few items he found valueless."), flee a winning fight ("...terminate this little contretemps..."), and make 30%/70% pass-through passes ("A 'lean and hungry' gentleman just wandered through..." / "The holder of the large bag just left..."). Also `DOME-FLAG` clearing when he grabs the rope
- ~~**Cyclops AI** – lack of proper threat response and interaction~~ ✅ `edges/cyclops-*.skein`
- ~~**Balloon mechanics** – launch, flight, and landing behavior incomplete~~ ✅ `edges/balloon.skein`, `deaths/volcano.skein`, `edges/gnome-*.skein`
- ~~**Machine room** – controls and effects not functional~~ ✅ `default.skein`
- ~~**Time tracking** – general clock events and fuses not fully implemented~~ ✅ fuses (`deaths/brick*.skein`), match burnout, lantern battery (`edges/lamp-dimming.skein`); candles still TODO (`hades.dg`)

## Former regressions (resolved)

Both items below used to fail but now match the recordings; kept for
historical context only.

1. ~~**Bat room contents** – `edges/bat.skein` #n2–n5 and `edges/bat.takeaway.skein` #n1 fail:
   jade figurine + garlic no longer listed in the Bat Room (figurine is still
   `(* is #in #bat-room)` in `autogen.dg:519`), the odor sentence is gone from
   the room look, and `take bat` now answers "You can't take the bat." instead
   of the old parser message.~~ ✅ all bat nodes match
2. ~~**Balloon death node** – `edges/balloon.skein` #n13: whitespace/formatting
   change and score 0 → 10 at rim-death. Likely a bless candidate.~~ ✅ node matches
