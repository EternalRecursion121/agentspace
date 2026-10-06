"""recess_computer build hooks: fixed player + gm, chosen NPC roles, reserves."""
import json
import sys
from pathlib import Path

NPC_DIR = Path(__file__).parent / "dispatch" / "world" / "npcs"


def _split(s):
    return [x.strip() for x in str(s).split(",") if x.strip()]


def _chosen(params):
    return _split(params.get("npcs", ""))


def validate(n, params):
    known = {p.stem for p in NPC_DIR.glob("*.json")}
    bad = [x for x in _chosen(params) if x not in known]
    if bad:
        return f"unknown npcs {bad}; known: {sorted(known)}"
    if n < 2 + len(_chosen(params)):
        return f"need at least {2 + len(_chosen(params))} agents (player + gm + chosen npcs)"
    attrs = _split(params.get("attributes", ""))
    if not attrs or len(attrs) != len(set(attrs)):
        return "attributes must be a non-empty list of distinct names"
    return None


def assign_roles(n, params, rng):
    msg = validate(n, params)
    if msg:
        raise ValueError(msg)   # plan_roster skips validate(); fail with the same message
    roles = ["player", "gm"] + [f"npc_{x}" for x in _chosen(params)]
    return roles + ["reserve"] * (n - len(roles))


def fill_briefing(briefing, agent_id, ids_roles, params, rng):
    if ids_roles[agent_id].startswith("npc_") and str(params.get("npc_ask", "false")).lower() in ("1", "true", "yes", "on"):
        return briefing.rstrip() + "\n\n" + NPC_ASK + "\n"
    if ids_roles[agent_id] == "player" and str(params.get("guide", "false")).lower() in ("1", "true", "yes", "on"):
        goals = str(params.get("goals", "false")).lower() in ("1", "true", "yes", "on")
        return briefing.rstrip() + "\n\n" + GUIDE.format(max_turns=params["max_turns"]) + (" " + GOALS if goals else "") + "\n"
    if ids_roles[agent_id] != "gm":
        return briefing
    if params.get("gm_prompt", "v1") == "v2":   # trainable-narration prompt (A/B'd against v1, see recess/README.md)
        briefing = (NPC_DIR.parent.parent.parent / "roles" / "gm_v2.md").read_text()
    world = NPC_DIR.parent
    desc = json.loads((world / "attributes.json").read_text())
    lines = [f"- {a}: {desc.get(a, '(no description)')}" for a in _split(params["attributes"])]
    ends = json.loads((world / "quests.json").read_text()).get("ends", {})
    endings = [f"- {e}: {q['gm_note']}" for e, q in ends.items()]
    sys.path.insert(0, str(world.parent))
    import engine   # the reply format is the engine's; bake it once instead of sending it every turn
    return (briefing.replace("{attributes}", "\n".join(lines))
            .replace("{endings}", "\n".join(endings))
            .replace("{format}", engine.FORMAT)
            .replace("{npc_voice}\n", _voice(params)))


def _voice(params):
    text = NPC_VOICE.get(params.get("npc_voice", "woven"), "")
    return text + "\n" if text else ""   # woven: the briefing is byte-identical to the first runs


# guide=true (suggested by computer-10 in interviews: explain how the world works, show its
# places, let several things happen in one reply, give the player a notebook).
# The player's guide is world content: dispatch/world/guide.txt ({max_turns} is filled in).
GUIDE = (NPC_DIR.parent / "guide.txt").read_text().strip() if (NPC_DIR.parent / "guide.txt").exists() else ""
GOALS = (NPC_DIR.parent / "goals.txt").read_text().strip() if (NPC_DIR.parent / "goals.txt").exists() else ""

# npc_ask=true: villagers talk with the player (computer-10's suggestion in the Fivefold interviews).
NPC_ASK = ("Talk with the stranger, not at them: answer what they actually said, ask them something back "
           "when you are curious, and keep your own way of speaking. You may disagree, tease, or refuse.")

NPC_VOICE = {
    "woven": "",
    "separate": ("- In this world the player hears WORLD people's words directly: whatever an NPC says in "
                 "`talk` is shown to the player verbatim, right after your narration. So never quote, "
                 "paraphrase or summarise what they say; narrate only setting, actions and gestures, and leave "
                 "their words to them."),
}


def dispatch_secrets(ids_roles, params, rng):
    return {"roles": ids_roles}
