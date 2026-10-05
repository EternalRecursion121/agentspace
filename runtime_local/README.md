# runtime_local — plain-mode scens without Docker

Runs a plain-mode dispatcher scen (`plain = true`, e.g. the recess family) in one
local process. The scen's `logic.py` and `dispatch/main.py` run unchanged against
`agentspace/dispatchlib.py`; only the transport differs. `LocalAdapter` implements
the adapter calls (`wake`, `collect`, `roll_session`, ...) over in-memory sessions.

- **GM, NPCs** (and optionally the player): OpenRouter chat models. The system prompt
  is the same file sandwich `runtime_pi/agentd.py` renders in plain mode (SOUL.md
  from the blank persona, ROLE.md with `fill_briefing`, WORLD.md). Sampling is fixed
  in `CHAT_SAMPLING` and written to `meta.json`.
- **computer-10 player** (`--player computer10`): `computer10.py` renders the player
  session in Computer's document format and samples `/v1/completions` on a vLLM
  server. World and role text are folded into the first `**User:**` turn; every
  delivery is a `**User:**` turn; replies are cut at any turn label Computer writes.
  An optional note from a previous playthrough (`--note-file`) is prepended to the
  first user turn, and every prompt is logged both with and without it.

```bash
export OPENROUTER_API_KEY=...
python3 runtime_local/localrun.py recess_computer runs/g1 --seed 1 --vllm-url http://127.0.0.1:8003
python3 runtime_local/chain.py recess_computer runs/chainA --rounds 3 --seed 21 --vllm-url http://127.0.0.1:8003
python3 runtime_local/localrun.py recess_computer runs/t1 --player deepseek/deepseek-v4.1-flash   # no GPU
```

Outputs per run: `meta.json`, `state.json`, `game_log.jsonl`, `transcript.md`,
`calls.jsonl` (every chat call) and `player_turns.jsonl` (computer-10: exact prompt,
prompt without the note, raw completion, parsed action, usage).

Not supported: messaging, tools, the public board, budgets, snapshots. It is a
research harness for single-player plain-mode worlds, not a replacement for PI.
