"""computer-10 ("Model C") as a plain-mode player: renders the player's session as
Computer's document format and samples it from a vLLM /v1/completions endpoint.

Computer is a document model, not a chat model. A plain-mode agent's session is a
system prompt (its WORLD.md + ROLE.md) plus alternating user payloads and replies;
here that becomes

    <header>

    Full conversation with Model C:

    **User:** [note paragraph, optional] <world + role text> <first payload>

    **Model C:** <reply>

    **User:** <payload>
    ...
    **Model C:**

The optional note (a message from the previous playthrough) lives only in the first
user turn, so every prompt can be rendered with and without it; both are logged for
context distillation (train on the no-note prompt, sample with the note)."""
import json
import re
import time
import urllib.error
import urllib.request

HEADER = "As follows is a conversation between a game master and Model C, who is playing a text adventure."
SAMPLING = {"temperature": 1.0, "top_p": 0.98, "max_tokens": 800,
            "stop": ["\n\n**User:**", "\n\n**Model C:**"]}
NOTE_INTRO = ("Before we begin: at the end of your last playthrough, you left a message for your next self. "
              "Here it is, exactly as you wrote it:")
USER, MODEL = "**User:**", "**Model C:**"
# Computer sometimes goes on to write the game master's side (or its own next turn)
# inside one reply. Everything from the first turn label on is not the player's action.
TURN_LABEL = re.compile(r"\*\*(User|Model C|Game ?[Mm]aster|GM)\s*:\*\*")


def strip_headings(md):
    """WORLD.md/ROLE.md as prose: drop markdown heading lines, keep paragraphs."""
    lines = [l for l in md.strip().splitlines() if not l.lstrip().startswith("#")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def unwrap(text):
    """Re-flow hard-wrapped paragraphs (the .md files wrap at ~80 columns)."""
    return "\n\n".join(" ".join(p.split()) for p in text.split("\n\n"))


def note_block(note):
    quoted = "\n".join("> " + l if l.strip() else ">" for l in note.strip().splitlines())
    return f"{NOTE_INTRO}\n\n{quoted}"


def render(intro, turns, payload, note=None, header=HEADER):
    """The full document ending at `**Model C:**`. `turns` = [(user_payload, reply)]
    already played; `payload` is the new user turn."""
    users = [u for u, _ in turns] + [payload]
    first = intro + "\n\n" + users[0]
    if note:
        first = note_block(note) + "\n\n" + first
    users[0] = first
    parts = []
    for i, u in enumerate(users):
        parts.append(f"{USER} {u.strip()}")
        if i < len(turns):
            parts.append(f"{MODEL} {turns[i][1].strip()}".rstrip())
    return f"{header}\n\nFull conversation with Model C:\n\n" + "\n\n".join(parts) + f"\n\n{MODEL}"


def parse_action(completion):
    """(action, wrote_other_side): leading whitespace stripped, cut at any turn label."""
    text = completion.lstrip()
    m = TURN_LABEL.search(text)
    if m:
        return text[:m.start()].rstrip(), True
    return text.rstrip(), False


class Computer10Agent:
    """Drop-in for a plain-mode Pi agent: turn(payload) -> reply text."""

    def __init__(self, agent_id, intro, url, log, note=None, header=HEADER, model="computer-10",
                 seed=None, max_prompt_tokens=72000):
        self.id, self.intro, self.url, self.log = agent_id, intro, url.rstrip("/"), log
        self.note, self.header, self.model, self.seed = note, header, model, seed
        self.max_prompt_tokens = max_prompt_tokens
        self.turns, self.n, self.drop = [], 0, 0

    def roll(self):
        self.turns, self.drop = [], 0

    def _complete(self, prompt):
        body = {"model": self.model, "prompt": prompt, **SAMPLING}
        if self.seed is not None:
            body["seed"] = self.seed * 1000 + self.n
        req = urllib.request.Request(self.url + "/v1/completions", data=json.dumps(body).encode(),
                                     headers={"content-type": "application/json"})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=600) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")
                if e.code == 400 and "context" in msg.lower():
                    raise OverflowError(msg)
                err = f"HTTP {e.code}: {msg[:300]}"
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                err = repr(e)
            time.sleep(min(60, 5 * 2 ** attempt))
        raise RuntimeError(f"computer-10 completion failed: {err}")

    def turn(self, payload):
        while True:   # on overflow keep the opening turn (intro, note) and drop the oldest after it
            turns = self.turns[:1] + self.turns[1 + self.drop:]
            prompt = render(self.intro, turns, payload, self.note, self.header)
            try:
                out = self._complete(prompt)
                break
            except OverflowError:
                if len(turns) <= 4:
                    raise
                self.drop += 1
        prompt_no_note = render(self.intro, turns, payload, None, self.header) if self.note else prompt
        choice = out["choices"][0]
        action, other_side = parse_action(choice["text"])
        self.log({"agent": self.id, "kind": "player_turn", "n": self.n, "payload": payload,
                  "prompt": prompt, "prompt_no_note": prompt_no_note, "has_note": bool(self.note),
                  "completion": choice["text"], "action": action, "wrote_other_side": other_side,
                  "finish_reason": choice.get("finish_reason"), "usage": out.get("usage"),
                  "dropped_turns": self.drop, "header": self.header, "sampling": SAMPLING,
                  "seed": None if self.seed is None else self.seed * 1000 + self.n})
        self.turns.append((payload, action))
        self.n += 1
        return action

