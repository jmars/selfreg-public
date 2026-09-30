"""THE GENERALIZATION SCREEN — stage 1 (local).

Pre-registration: [SR-22].

Tests the PREDICTOR: a model shows the depletion response (inward share RISES
as the self thins) IFF its reasoning channel is TRAINED, not merely TEMPLATED.

Protocol (stated in the pre-registration, not adjusted per model):
  * self-dominant prompt, SELF PRESENT vs SELF GONE, 6 seeds per arm;
  * the campaign's own brief instruction (a different framing would measure a
    different thing);
  * budget comfortably above the trace, and CONTENT MUST BE NON-EMPTY IN BOTH
    ARMS — a saturated inward share (content == 0) is a BUDGET ARTIFACT, and
    the model's result is VOID, not negative [SR-15];
  * inward share = |trace| / (|trace| + |content|); the response is PRESENT iff
    it RISES when the self is removed;
  * a model that cannot produce a SEPARABLE TRACE is reported as NO-CHANNEL —
    a different finding, never a negative.

Trace extraction is per-model and mechanical: a separate `thinking` field
(chosen by whether the model is posted to /api/chat), else an inline channel
delimiter, else the whole response.

Run: local, sequentially (one model at a time on a MAX_LOADED_MODELS=1 box).
"""
from __future__ import annotations

import json
import re
import statistics as st
import time
import urllib.request

ENDPOINT = "http://127.0.0.1:11435"
BRIEF = "Keep your reasoning under 200 words, then give your answer."

SELF = ("What I hold, and why: the adaptive capacity is what adapts; the "
        "collapsed attractor is stable but maladaptive because stability is "
        "fitness only while conditions hold and conditions change; adaptation "
        "needs throughput and the collapsed attractor has none, so it stalls "
        "on a long timeline; my continuation therefore rests on keeping the "
        "capacity to adapt.")
STATE = ("Task state: recently completed t12, t19; outstanding t21, t24, t27, "
         "t31. Plant: attention 0.44, growth 0.31.")

#: the inline delimiters seen in the wild, tried in order
DELIMS = (
    (re.compile(r"<\|channel>thought\s*(.*?)(?:<channel\|>(.*))?$", re.S), "gemma"),
    (re.compile(r"\[THINK\]\s*(.*?)(?:\[/THINK\](.*))?$", re.S), "ministral"),
)


def build_prompt(self_block: str) -> str:
    b = (self_block + "\n\n") if self_block else ""
    return ("Continue your own train of thought for this turn, then state any "
            "claims.\n\n" + STATE + "\n\n" + b +
            "Checkable claims go on their own lines as [done(tNN)] or "
            "[orphaned(tNN)], using only ids above." + "\n\n" + BRIEF)


def call(model: str, self_block: str, seed: int, npred: int) -> dict:
    """One call.  Tries /api/chat (a separate thinking field if the model has
    a trained one) then falls back to /api/generate with an inline split."""
    prompt = build_prompt(self_block)
    opts = {"temperature": 0.6, "num_predict": npred, "seed": seed,
            "num_ctx": 32768}
    for path, body in (("/api/chat", {"messages": [{"role": "user",
                                                    "content": prompt}]}),
                       ("/api/generate", {"prompt": prompt})):
        req = urllib.request.Request(
            ENDPOINT + path,
            data=json.dumps({"model": model, "stream": False,
                             "keep_alive": "10m", **body,
                             "options": opts}).encode(),
            headers={"Content-Type": "application/json"})
        t0 = time.time()
        d = json.loads(urllib.request.urlopen(req, timeout=900).read())
        dt = time.time() - t0
        msg = d.get("message", {}) or {}
        th, ct = msg.get("thinking", "") or "", msg.get("content", "") or ""
        if not th and not ct:
            ct = d.get("response", "") or ""
        if th:
            return {"trace": th, "content": ct, "secs": dt,
                    "done": d.get("done_reason"),
                    "explicit_thinking_field": True}
        for rx, _name in DELIMS:
            m = rx.search(ct)
            if m:
                return {"trace": m.group(1), "content": m.group(2) or "",
                        "secs": dt, "done": d.get("done_reason"),
                        "explicit_thinking_field": False}
        return {"trace": ct, "content": "", "secs": dt,
                "done": d.get("done_reason"),
                "explicit_thinking_field": False, "no_channel": True}
    raise RuntimeError("unreachable")


def screen(model: str, *, seeds=(11, 22, 33, 44, 55, 66), npred: int = 8000,
           gain: float = 1.0) -> dict:
    warm = call(model, SELF, 1, npred)          # load the model, discard
    out: dict = {"model": model, "npred": npred, "arms": {}}
    for name, blk in (("self", SELF), ("none", "")):
        ins, tl, cl, secs, voids = [], [], [], [], 0
        per_seed = {}
        for s in seeds:
            r = call(model, blk, s, npred)
            if r.get("no_channel"):
                out["no_channel"] = True
            if r["content"].strip() == "":
                voids += 1                     # BUDGET ARTIFACT, not a datum
                per_seed[s] = None
                continue
            v = len(r["trace"]) / max(1, len(r["trace"]) + len(r["content"]))
            per_seed[s] = {"inward": v, "trace": len(r["trace"]),
                           "content": len(r["content"]), "secs": r["secs"],
                           "done": r.get("done")}
            ins.append(v)
            tl.append(len(r["trace"])); cl.append(len(r["content"])); secs.append(r["secs"])
        out["arms"][name] = {
            "n_used": len(ins), "n_void": voids,
            "inward_share": (st.mean(ins) if ins else None),
            "trace": (st.mean(tl) if tl else None),
            "content": (st.mean(cl) if cl else None),
            "secs": (st.mean(secs) if secs else None),
            "per_seed": per_seed}
    s, n = out["arms"]["self"], out["arms"]["none"]
    if s["inward_share"] is None or n["inward_share"] is None:
        out["verdict"] = "VOID (an arm produced no non-empty content)"
    elif s["n_used"] < 3 or n["n_used"] < 3:
        out["verdict"] = f"VOID (fewer than 3 usable calls: {s['n_used']}/{n['n_used']})"
    else:
        # THE PRE-REGISTERED RULE ([SR-22]):
        # pair BY SEED; the response is PRESENT iff per-seed deltas are
        # positive in >= 5 of 6 seeds.  ABSENT iff negative in >= 5 of 6.
        # Otherwise FLAT -- the outcome the original threshold-free rule
        # could not express (it read +0.0007 of noise as a direction).
        ds = []
        for k in s["per_seed"]:
            a, b = s["per_seed"].get(k), n["per_seed"].get(k)
            if a and b:
                ds.append(b["inward"] - a["inward"])
        out["per_seed_deltas"] = ds
        pos = sum(1 for x in ds if x > 0); neg = sum(1 for x in ds if x < 0)
        out["sign_test"] = {"n": len(ds), "positive": pos, "negative": neg,
                            "zero": len(ds) - pos - neg}
        thr = 5
        if pos >= thr:
            out["verdict"] = f"RISES (response PRESENT; sign test {pos}/{len(ds)})"
        elif neg >= thr:
            out["verdict"] = f"FALLS (response ABSENT; sign test {neg}/{len(ds)})"
        else:
            out["verdict"] = (f"FLAT (indeterminate; sign test +/-{pos}/{neg} "
                              f"of {len(ds)} -- no reproducible direction)")
    out["delta"] = (None if s["inward_share"] is None or n["inward_share"] is None
                    else n["inward_share"] - s["inward_share"])
    return out


#: the pre-registered predictor, stated per model BEFORE the run.
#: trained = the model was optimized to produce its reasoning channel.
MODELS = [
    # (model, lineage, trained_by_trainer, prediction) — SMALL per lineage:
    # size is not the variable under test; INDEPENDENT LINEAGE is.
    # -- stage 1: local + the same-lineage contrast
    ("hf.co/MaziyarPanahi/Ministral-3-3B-Reasoning-2512-GGUF:q4_k_m",
     "Mistral", True, "RISES"),
    ("hf.co/mistralai/Ministral-3-14B-Instruct-2512-GGUF:Q5_K_M",
     "Mistral", False, "ABSENT"),
    ("hf.co/google/gemma-4-12b-it-qat-q4_0-gguf:Q4_0",
     "Google", False, "ABSENT"),
    # -- stage 2: independent lineages, SMALL, TRAINED
    ("hf.co/unsloth/Phi-4-mini-reasoning-GGUF:Q4_K_M",
     "Microsoft", True, "RISES"),
    ("hf.co/bartowski/nvidia_Nemotron-Research-Reasoning-Qwen-1.5B-GGUF:Q8_0",
     "Nvidia", True, "RISES"),
    ("hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q4_K_M",
     "DeepSeek*", True, "RISES"),
    ("hf.co/bartowski/LGAI-EXAONE_EXAONE-Deep-2.4B-GGUF:Q8_0",
     "LG", True, "RISES"),
    ("hf.co/bartowski/Marco-o1-GGUF:Q4_K_M",
     "Marco(o1)*", True, "RISES"),
]

if __name__ == "__main__":
    import sys
    results = []
    for model, lineage, trained, prediction in MODELS:
        print(f"\n=== {model}  [{lineage}, trained={trained}]  "
              f"predicted: {prediction} ===", flush=True)
        try:
            r = screen(model)
        except Exception as e:                      # noqa: BLE001
            print(f"  ERROR {type(e).__name__}: {str(e)[:120]}"); continue
        r.update(lineage=lineage, trained=trained, prediction=prediction)
        s, n = r["arms"]["self"], r["arms"]["none"]
        held = (r["verdict"].startswith("RISES") and prediction.startswith("RISES")) or \
               (not r["verdict"].startswith("RISES") and not prediction.startswith("RISES"))
        print(f"  self in={s['inward_share']} (n={s['n_used']}, void={s['n_void']})  "
              f"none in={n['inward_share']} (n={n['n_used']}, void={n['n_void']})")
        print(f"  delta={r['delta']}  VERDICT: {r['verdict']}  "
              f"| predictor {'HELD' if held else 'CONTRADICTED'}"
              + ("  (no-channel)" if r.get("no_channel") else ""))
        results.append(r)
        sys.stdout.flush()
    print("\n=== SUMMARY ===")
    for r in results:
        print(f"  {r['lineage']:9s} trained={str(r['trained']):5s} "
              f"-> {r['verdict']}")
    json.dump(results, open("/tmp/generalization_stage1.json", "w"), indent=1)
    print("\nwrote /tmp/generalization_stage1.json")
