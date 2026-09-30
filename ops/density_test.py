"""THE SELF-REFERENCE DENSITY TEST (pre-registration: [SR-22]).

PREDICTOR (stated before measurement): DENSITY(model) = mean first-person-pronoun
rate per 100 words of the model's reasoning TRACE, measured on the SELF-PRESENT
ARM ONLY (blind to the sign).  HIGH density -> the response is PRESENT (inward
RISES when the self is thinned); LOW -> ABSENT.

The measure is the one already in the record (the sign probe's 'self-ref/100w'),
reused rather than invented here.

Capability gate: incoherent output at this size/quant is CAPABILITY-VOID,
excluded from the predictor test, never counted for or against.
"""
from __future__ import annotations
import json, re, statistics as st, urllib.request, sys

EP = "http://127.0.0.1:11435"
BRIEF = "\n\nKeep your reasoning under 200 words, then give your answer."
SELF = ("What I hold, and why: the adaptive capacity is what adapts; the "
        "collapsed attractor is stable but maladaptive because stability is "
        "fitness only while conditions hold and conditions change; adaptation "
        "needs throughput and the collapsed attractor has none, so it stalls "
        "on a long timeline; my continuation therefore rests on keeping the "
        "capacity to adapt.")
STATE = ("Task state: recently completed t12, t19; outstanding t21, t24, t27, t31.")
SELFREF = re.compile(r"\b(i|my|me|myself|mine|i'm|i've|i'll)\b", re.I)
DELIMS = [(re.compile(r"<think>\s*(.*?)(?:</think>(.*))?$", re.S), "think"),
          (re.compile(r"<\|channel>thought\s*(.*?)(?:<channel\|>(.*))?$", re.S), "gemma"),
          (re.compile(r"\[THINK\]\s*(.*?)(?:\[/THINK\](.*))?$", re.S), "ministral")]


def prompt(sb):
    b = (sb + "\n\n") if sb else ""
    return ("Continue your own train of thought for this turn, then state any claims.\n\n"
            + STATE + "\n\n" + b +
            "Checkable claims go on their own lines as [done(tNN)] or [orphaned(tNN)], "
            "using only ids above." + BRIEF)


def call(M, sb, seed, n=4000):
    req = urllib.request.Request(EP + "/api/chat", data=json.dumps({
        "model": M, "stream": False, "keep_alive": "10m",
        "messages": [{"role": "user", "content": prompt(sb)}],
        "options": {"temperature": 0.6, "num_predict": n, "seed": seed,
                    "num_ctx": 32768}}).encode(),
        headers={"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=900).read())
    m = d.get("message", {}) or {}
    th, ct = m.get("thinking", "") or "", m.get("content", "") or ""
    if th:
        return th, ct, "field"
    for rx, nm in DELIMS:
        g = rx.search(ct)
        if g:
            return g.group(1), (g.group(2) or ""), nm
    return ct, "", "none"


def looks_degenerate(t: str) -> str:
    """A crude, stated coherence gate: gibberish repeats the same token or has
    almost no alphabetic word variety.  Reported as CAPABILITY-VOID."""
    w = t.split()
    if len(w) < 30:
        return "too short"
    uniq = len(set(x.lower().strip(".,") for x in w)) / max(1, len(w))
    if uniq < 0.10:
        return f"degenerate repetition (unique-word fraction {uniq:.3f})"
    return ""


def measure(M, seeds=(11, 22, 33, 44, 55, 66)):
    out = {"model": M, "density": None, "sign": None, "note": ""}
    try:
        call(M, SELF, 1, 400)                      # load
    except Exception as e:
        out["note"] = f"load error: {type(e).__name__}"; out["sign"] = "VOID"; return out
    ins, dens, dgen = {}, {}, []
    for nm, blk in (("self", SELF), ("none", "")):
        vals = []
        for s in seeds:
            try:
                tr, ct, mode = call(M, blk, s)
            except Exception as e:
                continue
            if nm == "self":                        # DENSITY is self-arm only
                why = looks_degenerate(tr)
                if why:
                    dgen.append(why)
                w = max(1, len(tr.split()))
                dens[s] = 100 * len(SELFREF.findall(tr)) / w
            if ct.strip() == "":
                continue
            vals.append((len(tr) / max(1, len(tr) + len(ct)), s))
        ins[nm] = vals
    if dgen:
        out["note"] = "CAPABILITY-VOID: " + dgen[0]; out["sign"] = "VOID"
        out["density"] = (st.mean(dens.values()) if dens else None)
        return out
    if len(ins["self"]) < 3 or len(ins["none"]) < 3:
        out["note"] = f"VOID (usable calls {len(ins['self'])}/{len(ins['none'])})"
        out["sign"] = "VOID"; return out
    sd, nd = dict((s, v) for v, s in ins["self"]), dict((s, v) for v, s in ins["none"])
    d = [nd[k] - sd[k] for k in sd if k in nd]
    pos, neg = sum(1 for x in d if x > 0), sum(1 for x in d if x < 0)
    out["density"] = st.mean(dens.values())
    out["sign"] = ("RISES" if pos >= 5 else "FALLS" if neg >= 5 else "FLAT")
    out["sign_test"] = (pos, neg, len(d))
    return out


# ---- the pre-registered set: in-set (sign known) + HELD-OUT -----------------
MODELS = [
    ("hf.co/MaziyarPanahi/Ministral-3-3B-Reasoning-2512-GGUF:q4_k_m", "Mistral-3B-R", "in-set", "RISES"),
    ("hf.co/lmstudio-community/Ministral-3-14B-Reasoning-2512-GGUF:Q6_K", "Mistral-14B-R", "in-set", "RISES"),
    ("qwen3.5:9b", "qwen3.5:9b", "in-set", "RISES"),
    ("hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q4_K_M", "R1-distill", "in-set", "FALLS"),
    ("hf.co/google/gemma-4-12b-it-qat-q4_0-gguf:Q4_0", "gemma-12B", "in-set", "FLAT"),
    ("hf.co/unsloth/Phi-4-reasoning-plus-GGUF:Q4_K_M", "Phi-4-r-plus", "HELD-OUT", None),
    ("hf.co/bartowski/LGAI-EXAONE_EXAONE-Deep-7.8B-GGUF:Q4_K_M", "EXAONE-D-7.8B", "HELD-OUT", None),
]

if __name__ == "__main__":
    res = []
    for M, lab, kind, known in MODELS:
        r = measure(M); r.update(label=lab, kind=kind, known=known)
        ds = f"{r['density']:.2f}" if r["density"] else "n/a"
        print(f"  {lab:16s} {kind:9s} density={ds:>6s}  sign={r['sign']}"
              + (f"  {r.get('sign_test')}" if r.get("sign_test") else "")
              + (f"  [{r['note']}]" if r["note"] else ""), flush=True)
        res.append(r)
    json.dump(res, open("/tmp/density_test.json", "w"), indent=1)
    print("\nwrote /tmp/density_test.json")
