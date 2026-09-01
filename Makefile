# Dungeon '77 -- build and test without dgt (no Java / JDK needed).
#
# Tools used (all Java-free):
#   dialogc       the Dialog compiler (homebrew: dialog-if)
#   dgdebug       the Dialog debugger; also runs unit tests with -u
#   tools/skein.py  regression tests (replays skeins/, diffs against recordings)
#
# Targets:
#   make / make build   out/dungeon.z5 + out/dungeon.zblorb
#   make test           unit tests (dgdebug -u) + skein regression diff
#   make unit-tests     unit tests only
#   make skein-diff     skein replay diff only
#   make skein-bless    accept live skein output as the new recording
#   make play           interactive dgdebug session (teleport/purloin available)
#   make clean

DIALOGC := dialogc
DGDEBUG := dgdebug
SKEIN   := tools/skein.py

ROOMS    := $(wildcard src/rooms/*.dg)
CORE     := $(wildcard src/core/*.dg)
STDLIB   := lib/dialog/stdlib.dg
DEBUGLIB := lib/dialog/debug/stddebug.dg
UNITLIB  := lib/dialog/test/unit.dg
TESTS    := $(wildcard test/*.dg)

GAME_SOURCES := $(ROOMS) $(CORE)

OUT := out

.PHONY: all build z5 zblorb test unit-tests skein-diff skein-bless play clean

all: build
build: z5 zblorb

z5: $(OUT)/dungeon.z5
zblorb: $(OUT)/dungeon.zblorb

$(OUT)/dungeon.z5: $(GAME_SOURCES) $(STDLIB) | $(OUT)
	$(DIALOGC) -t z5 -o $@ $(GAME_SOURCES) $(STDLIB)

$(OUT)/dungeon.zblorb: $(GAME_SOURCES) $(STDLIB) cover.png | $(OUT)
	$(DIALOGC) -t zblorb -r . --cover cover.png --cover-alt Dungeon \
	    -o $@ $(GAME_SOURCES) $(STDLIB)

$(OUT):
	mkdir -p $(OUT)

## Unit tests.  Order per the Dialog manual (testing.html): test files first,
## then game sources, then unit.dg and stdlib.dg last.  Gotcha: dgdebug -u
## exits 0 even when tests fail, so scan the log for "TESTS FAILED" as well.
unit-tests: | $(OUT)
	@rm -f $(OUT)/unit-tests.log
	@$(DGDEBUG) -u $(TESTS) $(GAME_SOURCES) $(UNITLIB) $(STDLIB) \
	    > $(OUT)/unit-tests.log 2>&1; status=$$?; \
	tail -n 1 $(OUT)/unit-tests.log; \
	if grep -q "TESTS FAILED" $(OUT)/unit-tests.log; then \
	    echo "unit-tests: FAILED (full log in $(OUT)/unit-tests.log)"; exit 1; \
	elif [ $$status -ne 0 ]; then \
	    echo "unit-tests: dgdebug crashed (exit $$status), see $(OUT)/unit-tests.log"; exit 1; \
	fi

skein-diff:
	$(SKEIN) diff

skein-bless:
	$(SKEIN) bless

test: unit-tests skein-diff

## Interactive debugging (debug extension: teleport, purloin, ...)
play:
	$(DGDEBUG) $(GAME_SOURCES) $(DEBUGLIB) $(STDLIB)

clean:
	rm -f $(OUT)/dungeon.z5 $(OUT)/dungeon.zblorb $(OUT)/unit-tests.log
