# Dungeon '77

This is a hand-ported version of *Dungeon* (aka *Zork*) to
[Dialog](https://github.com/Dialog-IF/dialog/)
from the MDL source backed up on 1977-12-12.

I attempted to use the Dialog stdlib features where possible, so some things
differ a bit. For example, the stdlib automatically opens doors, so you can
just walk west through the window (actually I guess this should be fixed)

## How to Build Locally

Install the [https://github.com/hlship/dialog-tool](Dialog tool).

Run:
```
dgt build
dgt test
dgt debug
```

For more, see the
[https://dialog-if.github.io/manual/dialog/1c03-dev/software.html](Dialog docs).


## Not yet implemented / TODO

* Lots of things off of the main happy path.

* I could only get 460 points out of 500, so some points may be missing.

* Container capacity and inventory load.

* Light source dimming warnings.

* Thief logic is simplified, he doesn't round-robin every non-sacred room
  like in the original. There are also some behaviors not implemented
  like throwing (btw there's no egg in the 1977 version)

* Cyclops also has lots of missing behaviors.

* In Dialog you `TELL SOMEONE TO DO SOMETHING` instead of `TELL SOMEONE "DO SOMETHING"`.
  It would be nice to support both ways.

* Each dynamic attribute uses 2 bytes of heap per object, bad on 8-bit
  platforms.  The timer feature is sparsely used and could be optimized.
