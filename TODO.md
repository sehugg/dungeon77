# TODO.md - Outstanding Tasks for Dungeon Port

## 1. Object Action Routines (Missing)

- **MIRROR-MIRROR** – `src/rooms/mirror.dg`
- **ROBBER-FUNCTION** – `src/rooms/thief.dg`
- **BALLOON** – `src/rooms/volcano.dg`
- **TUBE-FUNCTION** – `src/rooms/volcano.dg`
- **WIRE-FUNCTION** – `src/rooms/volcano.dg`
- **CYCLOPS** – `src/rooms/cyclops.dg`
- **CHALICE** – `src/rooms/treasure-room`
- **HEAD-FUNCTION** – `src/rooms/cyclops.dg`
- **BODY-FUNCTION** – `src/rooms/hades.dg`
- **CYCLOPS-ROOM** – `src/77act1.mud`
- **COKE-BOTTLES** – `src/rooms/coalmine.dg`
- **GHOST-FUNCTION** – `src/rooms/hades.dg`
- **BODY-FUNCTION** – `src/rooms/hades.dg`
- **DDOOR-FUNCTION** – `src/rooms/hades.dg`
- **FLY-ME** – `src/rooms/autogen.dg`
- **STICK-FUNCTION** – `src/rooms/autogen.dg`
- **DUMBWAITER** – `src/rooms/autogen.dg`
- **NO-OBJS** – `src/rooms/autogen.dg`, `src/rooms/coalmine.dg`, etc.
- **MACHINE-ROOM** – `src/rooms/machine.dg`
- **MSWITCH-FUNCTION** – `src/rooms/machine.dg`
- **FLASK-FUNCTION** – `src/rooms/autogen.dg`
- **EATME-FUNCTION** – `src/rooms/autogen.dg`
- **CAKE-FUNCTION** – `src/rooms/autogen.dg`
- **LEAD-GATE** – `src/rooms/dam.dg`
- **MATCH-FUNCTION** – `src/rooms/dam.dg`
- **BOLT-FUNCTION** – `src/rooms/dam.dg`
- **LEAK-FUNCTION** – `src/rooms/dam.dg`
- **LEDGE-FUNCTION** – `src/rooms/volcano.dg`
- **CYCLE-PRIMARY** – `src/77act1.mud`
- **CYCLOPS-FLAG** – `src/rooms/cyclops.dg`
- **MAGIC-FLAG** – `src/rooms/cyclops.dg`
- **EMPTY-HANDED** – `src/rooms/coalmine.dg`, `lower-shaft`, `dead-end5`, etc.

## 2. Room Action Routines (Missing)

- **DAM-ROOM** – `src/rooms/dam.dg`
- **MAINT-ROOM** – `src/rooms/dam.dg`
- **MACHINE-ROOM** – `src/rooms/machine.dg`
- **LLD1-ROOM** – `src/rooms/hades.dg`
- **LLD2-ROOM** – `src/rooms/hades.dg`
- **TREASURE-ROOM** – `src/77act1.mud`
- **BOOM-ROOM** – `src/77act2.mud`
- **TIME** – `src/77act1.mud` (mine-entrance)
- **NO-OBJS** – `src/rooms/autogen.dg`, `src/rooms/coalmine.dg`, etc.
- **CYCLE-PRIMARY** – `src/77act2.mud`
- **CYCLOPS-FLAG** – `src/77act1.mud`
- **MAGIC-FLAG** – `src/77act1.mud`
- **FROBOZZ** – `src/77act1.mud` (autogen)
- **RIDDLE-FLAG** – `src/77act1.mud`

## 3. Flag & Conditional Logic

- `CYCLOPS-FLAG` – Cyclops presence/state
- `MAGIC-FLAG` – Magic item availability
- `EMPTY-HANDED` – Weight limit enforcement (multiple rooms)
- `DOME-FLAG` – Volcano danger state
- `LLD-FLAG` – Hades room lock state
- `RIDDLE-FLAG` – Riddle puzzle activation
- `FROBOZZ` – Frobozz flag (autogen)

## 4. Critical Bugs / Quality Issues

- **Combat continues after death** – `src/core/melee.dg`
- **Performance bottleneck** – `src/core/melee.dg` (combat table lookup)
- **Weapon management** – `src/core/melee.dg` (unwield, tracking)
- **Darkness handling** – many rooms lack proper enforcement
- **Thief logic** – missing `ROBBER-FUNCTION` and related mechanics
- **Cyclops AI** – cyclops behavior not fully implemented
- **Balloon physics** – launch, ascent, descent, and landing not functional
- **Machine room** – machine controls and effects incomplete
- **Score/point system** – some rooms lack final scoring logic

## 5. Feature Gaps

- **Darkness system** – rooms not properly dark-enforced
- **Thief mechanics** – robbing, item movement, and AI missing
- **Cyclops AI** – lack of proper threat response and interaction
- **Balloon mechanics** – launch, flight, and landing behavior incomplete
- **Machine room** – controls and effects not functional
- **Time tracking** – general clock events and fuses not fully implemented
