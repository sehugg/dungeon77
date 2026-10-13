# Dungeon '77

This is a mostly hand-ported version of *Dungeon* (aka *Zork*) to
[Dialog](https://github.com/Dialog-IF/dialog/)
from the MDL source backed up on 1977-12-12.

I attempted to use the Dialog stdlib features where possible, so some things
differ a bit. For example, the stdlib automatically opens doors, so you can
just walk west through the window (actually I guess this should be fixed)

## How to Build Locally

Just type "make".

For more, see the
[https://dialog-if.github.io/manual/dialog/](Dialog docs).

## Tools

`tools/skein.py` -- A Python CLI version of the Dialog skein tool, with lots
of features.

`tools/ascii2dlg.py` -- Dialog doesn't support fixed-width text or
`<pre>` so this is a workaround.


## Not yet implemented / TODO

* Lots of things off of the main happy path. I could only get 460 points out of 500.

* Container capacity and inventory load.

* Thief logic is simplified.

* In Dialog you `TELL SOMEONE TO DO SOMETHING` instead of `TELL SOMEONE "DO SOMETHING"`.
  It would be nice to support both ways.

* Each dynamic attribute uses 2 bytes of heap per object, bad on 8-bit
  platforms.  The timer feature is sparsely used and could be optimized.
  (Better yet, the Dialog compiler could have a more efficient representation for 
  sparse attributes)
