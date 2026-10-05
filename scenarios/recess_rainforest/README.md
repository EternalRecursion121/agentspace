# Fivefold (`recess_computer`)

A small text adventure built for computer-10 ("Model C", a document model with no
assistant training) as the player. Same engine as `recess_mvp` (copied, not
shared), five NPC agents, an LLM game master, and one addition: an optional
**handoff** wake after the game that asks the player for a single message to its
next self, for iterated play ("begin again, over and over, with one message
passed between").

## The world

Fivefold is a hamlet where five paths meet at a crossing. The paths *drift*: at
dusk a path may lead a little differently than it did. At the crossing stands the
Waystone, carved with one line from each traveller for whoever comes after, kept
by Aud the stonecutter. Uphill, Ottilie Vane has spent fifty years mapping the
drift; her great map lacks one corner, the country the sixth path reaches. That
path appears beside the blank signpost only at dusk. Brann ferries people to Tern
Island for a fare of one true thing about themselves; on the island an older map
is scratched into a broken tower. Ines keeps bees whose comb is built in the shape
of the paths. Pell, ten, lays a stone from every path on the mill floor every day,
and knows a gap beneath the millstones that leads down to the knot, where the
paths are rooted.

What there is to decide: whether the map should be finished and laid on the pool
in the knot, pinning every path for good (`map_pinned`), or left unfinished so the
valley keeps drifting (`drift_kept`); whether to take Brann's ferry pole so he can
leave (`ferry_taken`); whether to walk the sixth path out (`walked_on`). None is
required. Endings are allowed from turn 15; the default cap is 40 turns.
Schedules: Pell finds the player at turn 10, dusk falls at 18, Ottilie comes down
to settle the map at 28.

16 places, 5 NPCs (`ottilie, brann, ines, pell, aud`), attributes honesty,
compassion, curiosity, patience, mischief, generosity.

## Running

Under the PI runtime it builds like any recess scen (7 agents: player, gm, five
NPCs; any OpenRouter player). For computer-10 as the player, use the local runner:

```bash
python3 runtime_local/localrun.py recess_computer runs/g1 --seed 1 --vllm-url http://127.0.0.1:8003
```

See `runtime_local/README.md`.

## Changes from recess_mvp's dispatcher

- `HOME` can be set with `DISPATCH_HOME` (the local runner runs outside a container).
- The player is told `[The game has ended.]` on the turn cap too, not only on an ending.
- After the game, the player's reply to the last delivery is kept (`final_reply`),
  and if `handoff` is on (default) the player is woken once more with the handoff
  prompt; the reply is `state["handoff"]` and goes into `transcript.md`.
