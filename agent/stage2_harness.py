"""STAGE-2 HARNESS — the turn loop that couples the halves.

A Stage-2 run is a sequence of DMN turns.  Each turn: the (stub) DMN
emits an AssertionBatch; the CEN checks it, writes the two classes
atomically, and returns verdicts; the plant advances one Stage-1 step.
The SN's own per-step machinery (floor / actuator / write-block, ZOH
state advance) is Stage 1's, imported and untouched.

THE COUPLING DECISION THIS MODULE OWNS — ROUND 2: ONE c, AND IT IS THE
PLANT'S SWITCH STATE.  harness.switch_c IS the frozen model's
cannibalization switch (dpdr/model.py:92-94): Theta_eff = Theta*S/S_rest,
c = sigma_c*max(0, tanh((E - Theta_eff)/w)) clipped to [0,1] — and the
harness's own per-substep code uses ONE c_sub for BOTH of the model's
jobs: the attention pinning k_in*(a_hold + mon_cost + chi*c_sub) AND the
lag target of the backlog state (B = EMA_tauD(c_sub), harness.py:306-351),
whose model-scale B is dimensionless in [0,1], A_eff = A + B
(harness.py:52-64).  THE COUPLED ARM THEREFORE RUNS THE HARNESS'S OWN
EDGE (edge_on) AND INJECTS NOTHING THROUGH THE SCHEDULE'S 'A' PORT.
Round 1 injected a second arrival term (B = EMA(u/n), the CEN's measured
unchecked share) while the pinning still read the plant's c — ONE model
variable split into two — and the model's mechanism cannot fire from two
numbers: c raising D and pinning attention is a statement about ONE
quantity.  Its measured signature was the WRONG SIGN: SPEC came out
PROTECTIVE (G_end 0.8895 vs OFF 0.8855), because the injected rise in D
reached the plant through the tanh(E/Es) production term with no
corresponding pinning of attention.
couple_backlog IS THEREFORE THE EXPERIMENT'S COUPLING SWITCH and the only
thing that differs between the arms: =True -> edge_on = cfg.edge, so
A_eff = A + B with B the plant's own c-EMA (exp22's SPEC arm); =False
(DEFAULT) -> the coupling is REMOVED (edge_on = False, A_eff = A), which
is exp22's OFF arm.  cfg.edge stays the Stage-1 master switch (no edge at
all when False).
THE SUBSTRATE'S MEASURED RATE IS TELEMETRY ONLY, AND THAT IS A STATED
GAP.  The CEN measures, per turn, the UNCHECKABLE share of what the
generator offered (u/n) — the substrate's real reading of
"unchecked-self-content arrival" — and `backlog_rate` carries it, EMA'd
at 1/tau_D.  It DRIVES NOTHING: the frozen model has no CEN, its c is a
function of the plant's own (E, S), and the model's pinning channel reads
that same c.  So in this wiring the generator's output has NO PATH INTO
THE PLANT — the CEN's backlog (and the routing law built on it) is an
OBSERVATION of the plant, not an actuator on it.  That consequence is
stated, not smoothed (§1a), and it is the price of NOT splitting the
model's variable.  `backlog_ema` (the raw backlog STOCK, one level
coarser) is the same telemetry and is explicitly NOT the model's B:
feeding the stock count as the addend saturated D (measured A_eff = 35.91
against the model's B <= 1; D = 0.99316 against the model's own
D*(B=1) = 0.8387).

WHERE THE SN's FLOOR LIVES.  The plant's switch is the MODEL'S — no floor
(SNConstants.from_params(p, floor=None), supplied HERE by the caller: the
baselined harness.py is untouched and its default behaviour with
AgentConfig() is unchanged, as is the baselined stage1_fix_tests X1(b),
which already constructs SNConstants(floor=None)).  The floor's licensed
home is the SN's OWN ACTIVATION BELIEF — the regulator's written-down
constant, existence-semantic (floors 0.5-1.3 escape identically,
floor_crit 0.4795 ~= the stuck error E* 0.4969) and never re-checked (a
floor held with a discrepancy monitor fails at kc ~ 0.2, exp6 part d /
handoff-selfreg-knowingfloor) — carried here as SN_ACTIVATION_FLOOR and
reported by the runner.  It is NOT fed to the plant's arming level, which
would pin Theta_eff at 0.7 for the whole inward range (0.8*S < 0.7 for
every S < 0.875) and delete exactly the state-dependence R2's law and the
model's collapse both rest on; and it is NOT fed to the router's gate
either (a gate on a level the protected mechanism does not use is the
thetafix class).  The seat that WOULD exercise it — the regulator's own
knowing-cost accounting — is measured to fail at kc ~ 0.2 and is NOT
built: a stated gap, not a silently dropped unit.

C8 LIVES HERE, as the resume path.  run_stage2 returns a Stage2State;
that object — not the returned log — is what a resumed session rebuilds
from.  stage2_tests part S2 asserts the resumed INTEGRATED state equals
the never-interrupted one at every field the next turn reads, NOT that
the logs match: the measured failure this encodes (artifact 1) had
gen-2's solver reading M_self[0] = 0.000000 against a recorded carry of
0.286782 — the state was logged beside the integration, never threaded
in, and a log-reading test PASSED while the solver was wrong.

THE DMN'S PER-TURN CONTEXT (the generator's seat, §11d's generator
subsection).  Each turn the DMN is handed ONE dict: the cross-boundary
plant snapshot (`last_plant`) plus `retrieved_self` — the previous
turn's `RetrievalOutcome.reconstruction.text`, which had no consumer
until now.  Retrieval stays PRICED (charged first inside check_turn);
this hop is the wiring, never a free side channel.  With the retrieval
seat off, `retrieved_self` is "" and the context is the pre-retrieval
one, unchanged.

EVIDENCE MARKING.  PROJECTION throughout: the loop runs and the
invariants hold.  The DMN generator now EXISTS (agent/dmn_llm.py,
opt-in through Stage2Config.dmn and HANDED IN — the harness still
constructs no LLM and holds no endpoint), but there is no WIDENED
assessment and no agent-level claim.  The
Datalog engine is REAL behind the Protocol when Stage2Config.
engine="real" (cen_real_engine.py, the C10 substitution; default
"stub"); the mechanism's dynamical claims remain Stage 1's, on the
frozen plant.

THE TWO ROUTING MODES (§11d; the R5 coupling, STATED — it used to be a
hidden requirement with an unattributable crash).  ROUTING OFF (no
selector injected, the DEFAULT) = NO SELECTOR = ROUTE-ALL: every valid
span routes (`interleave.build_batch(selected=None)`, f == 1), there is
nothing that decides a split, and a stream-emitting DMN is ACCEPTED
directly — a raw `str` from the DMN is extracted and route-all'd in the
loop, exactly as `dmn_llm.stream_to_batch` would.  ROUTING ON (a
selector injected) = THE EXTERNAL SELECTOR DECIDES: the selector maps
this turn's extracted spans to content-blind SpanStates and returns the
routed positions, so the DMN must hand over its raw stream and the
harness — not the DMN — builds the batch; an `AssertionBatch` there is
refused.  ROUTING OFF is the mode the pre-registered agent experiment's
'direct replica of exp22' arm requires (handoff-selfreg-agentexp-plan);
ROUTING ON is the 'realistic system' arm.  A DMN emitting neither a
`str` nor an `AssertionBatch`, or the wrong one for the mode, raises
`ChainError` NAMING the mode and the adapter — never an AttributeError
from deep inside the CEN.

THE ROUTING SEAT (R5, §3a / §11d; item 'extractor').  Stage2Config.
routing_selector — DEFAULT None — INJECTS an externally-built
routingcrit.RoutingSelector (the harness never constructs one: R5 keeps
the selector outside the mechanism's write domain).  With a selector
attached the turn loop: consolidates the R2 window at each
consolidation boundary (tau_S = TAU_S_TURNS = 100 turns) AND at the
first turn of a fresh state, calls RoutingWindow.consolidate with
G=None (the G-analogue is UNSOLVED — the maximally conservative arm,
recorded per turn, never a fabricated G), RELOADS the versioned
criterion ONLY at those boundaries (R2's timescale), maps each turn's
extracted spans to content-blind SpanStates, and builds the batch with
the selector's `selected` positions — so unselected valid spans
re-enter the prose verbatim and never reach the checker.  With routing
attached the DMN must emit its raw free-form STREAM (a str): the
EXTRACTOR, not the DMN, decides what is a claim.  The default (no
selector) path is byte-identical to the pre-routing loop — no
criterion is read, no directory is created, and `Stage2LogRow.routed`
is 0.

THE OUT-OF-PROCESS BOUNDARY (item 13a, §3a R6 v1; DEFAULT OFF).  R6
requires the criterion, the held-out definition and the integrity
anchor to be owned OUT-OF-PROCESS before the mechanism executes code,
because in-process no boundary can hold (MEASURED: R11, a fresh store
plus a token it NAMES "designer" publishes f_max=0.0 over the sealed
v1 and takes the loop 3/3 -> 0/0).  `Stage2Config.routing_via_boundary`
swaps the ROUTING seat's two decision points for calls to a separate
daemon process over an AF_UNIX socket: the criterion READ
(`Stage2State.reload_criterion`, still only at a consolidation
boundary) and the SELECTION (`_plan_routing_boundary` — the daemon
extracts, maps to SpanStates, applies the rule and the [f_min, f_max]
CLIP, and returns positions).  This process then holds NO selector
object and reads NO criterion file.  FAIL-CLOSED: every boundary
failure raises BoundaryUnavailable (a ChainError) and the run STOPS —
there is deliberately NO local fallback, because a fallback would
reopen the forged-publish path behind a runtime flag.  The default
(routing_via_boundary=False) is the pre-boundary loop BYTE-IDENTICALLY:
no client is constructed, no socket is opened, and no new import runs.
WHAT v1 DOES NOT CLOSE is stated in boundary_client.py's docstring and
in the battery (stage2_boundary_tests.py): the criterion and the
held-out definition stay mechanism-READABLE by design, the OS-user
residual is re-based to the daemon's uid rather than removed, and the
shim itself is in-process code.  R6 v1 must not be cited as closing
more than that.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
from dataclasses import dataclass, field, replace
from typing import Callable

from dpdr.model import Params, Schedule

from cen import (AdmissibleLevers, Assertion, AssertionBatch, CEN,
                 ChainError, CostBudget, DurableRecord, LeverProposal,
                 StubDatalogEngine, WriterToken)
from harness import Agent, AgentConfig, H_STEP
from sn import SNConstants, zoh_lag


def parse_tool_blocks(stream: str):
    """LAZY forward to `realtools.parse_tool_blocks` (worker
    prerequisite 3).  A function, not an import: the DEFAULT path must
    not even load the tool layer (the vocation/actions import
    discipline — a default run's imports are part of its byte
    identity, asserted by the batteries)."""
    from realtools import parse_tool_blocks as _ptb
    return _ptb(stream)

__all__ = ["Stage2Config", "Stage2State", "run_stage2", "Stage2LogRow",
           "checkpoint_read_surface", "TAU_S_TURNS", "SN_ACTIVATION_FLOOR",
           "agent_config_for_stage2"]

#: THE SN'S ACTIVATION BELIEF — the regulator's OWN written-down floor,
#: NOT the plant's arming level (see the module docstring).  It keeps
#: sn.py's own value and its licensing: existence semantics (floors
#: 0.5-1.3 escape identically; floor_crit 0.4795 ~= the stuck error
#: E* 0.4969), held as a CONSTANT and never re-checked, because a floor
#: held with a discrepancy-monitoring cost FAILS at kc ~ 0.2
#: (handoff-selfreg-knowingfloor; exp6 part d).  The plant it protects
#: runs the FROZEN model's floorless switch (dpdr/model.py:92-94) — the
#: substrate's ACTUAL arming level, which is what the routing law is
#: told.  MEASURED-constant, INTERPRETATION as a belief, PROJECTION as a
#: mechanism until a knowing-cost seat is built (stated gap).
SN_ACTIVATION_FLOOR = float(SNConstants().floor)          # 0.7

def agent_config_for_stage2(p: Params, cfg: "Stage2Config") -> AgentConfig:
    """THE STAGE-2 PLANT'S CONFIG — the ONE place its arming level is set.

    The plant runs the FROZEN MODEL's switch: `SNConstants.from_params(p,
    floor=None)` (dpdr/model.py:92-94 has no floor), supplied HERE by the
    Stage-2 caller so that the baselined `harness.py` default
    (`AgentConfig()` -> floor 0.7) is untouched.  The coupling is the
    model's own: `edge_on = cfg.edge and cfg.couple_backlog`, i.e. ONE c
    (the plant's switch state) drives both the attention pinning and the
    demand addend `B = EMA_tauD(c)`, and `couple_backlog=False` means the
    coupling is REMOVED (`A_eff = A`) — exp22's OFF arm.

    It is a function, not an inline expression, because a SECOND caller
    must read the same level without constructing the plant: the routing
    law is told `AgentConfig.sn.floor` off the plant it protects, and the
    pilot's diagnostics report it.  Two expressions of the same constant
    is how a gate and its mechanism drift apart (thetafix class).
    """
    return AgentConfig(regulator_on=cfg.regulator,
                       edge_on=(cfg.edge and cfg.couple_backlog),
                       sn=SNConstants.from_params(p, floor=None))


#: R2's consolidation timescale, expressed in TURNS: tau_S = 100 t.u.
#: and the harness maps one turn = one tau_a step (the F4 convention),
#: so one consolidation window is TAU_S_TURNS turns.  The routing
#: window's f is set once per window (routing.RoutingWindow), never per
#: turn — this constant is the only place the mapping is stated.
TAU_S_TURNS = 100


@dataclass
class Stage2Config:
    """Stage-2 switches.  Everything genuinely new is DEFAULT OFF or
    stubbed; the defaults reproduce Stage-1 behaviour with the CEN
    scaffolding observing."""
    # -- the plant loop (Stage 1, imported read-only) ---------------------
    regulator: bool = True          # Stage-1 AgentConfig default
    # the Stage-1 G->D edge (A_eff = A + B, B = the EMA at tau_D of the
    # PLANT'S OWN switch state c — the model's ONE c, which also drives
    # the attention pinning; see the module docstring).  It is the
    # master switch for the edge's existence.
    edge: bool = True
    # THE EXPERIMENT'S COUPLING SWITCH — the ONLY difference between the
    # pre-registered arms (SPEC vs OFF).  =True: the coupling is ON
    # (edge_on = cfg.edge), so A_eff = A + B with B the plant's own
    # c-EMA — exp22's SPEC arm.  =False (DEFAULT): the coupling is
    # REMOVED (edge_on = False, A_eff = A) — exp22's OFF arm.  NOTHING is
    # injected through the schedule's 'A' port any more: a second
    # arrival term beside the plant's c is exactly the split of the
    # model's ONE variable that round 1 introduced (measured signature:
    # SPEC came out PROTECTIVE, the wrong sign).
    couple_backlog: bool = False
    # -- the CEN side ------------------------------------------------------
    budget: CostBudget = field(default_factory=CostBudget)
    levers: AdmissibleLevers = field(default_factory=AdmissibleLevers)
    record_path: str = ""           # empty -> ephemeral tmp file (cleaned
                                    # up unless keep_record)
    keep_record: bool = False
    # the DMN turn emitter: (turn, plant snapshot) -> AssertionBatch.
    # None -> the stub DMN below (NO LLM; the P4 compiler does not exist).
    dmn: Callable[[int, dict], AssertionBatch] | None = None
    # ENGINE SUBSTITUTION (C10): "stub" (default, unchanged) or "real"
    # -> DatalogDatalogEngine over the verified dlb binding (its own
    # durable store directory — C15, never the shared fx-agent-memory
    # store).  A real engine that cannot load its library fails LOUD
    # (DlLibraryError at import); there is NO silent stub fallback.
    engine: str = "stub"
    # the real engine's store directory (C15).  "" -> ephemeral per-run
    # tmp dir (cleaned up unless keep_record); ignored when engine="stub".
    store_dir: str = ""
    # -- the retrieval layer (item 'retrieval'; DEFAULT OFF, the same
    # convention as couple_backlog: the pre-retrieval turn loop is the
    # verified baseline) --------------------------------------------
    # retrieval_priced: charge the per-turn retrieval in the SAME C11
    # ledger, FIRST (the standing-cost reconciliation — see retrieval.py)
    retrieval_priced: bool = False
    # retrieval_decay: the C20 retrieval-weight decay rate applied at
    # consolidation.  Default 1.0 = NO decay (C20 err slow); the
    # budget-derived form is retrieval.derive_decay_rate(B, N_ss).
    # A decay != 1.0 REQUIRES retrieval_priced=True: an unpriced seat is
    # the CONTROL ARM ONLY (it still reconstructs, at zero charge), so
    # Stage2State REFUSES the (decay, unpriced) combination rather than
    # pricing it behind the caller's back.
    retrieval_decay: float = 1.0
    # -- the AUTOMATIC, CONTEXT-CUED injection seat (assoc.py; the
    # memory term's missing half).  retrieval_seat: an EXTERNALLY-BUILT
    # ContextCueSeat, injected the way routing_selector is — the
    # harness NEVER constructs one, and the cue policy stays the
    # caller's (R5 reframed: the externally-owned object is the CUE
    # FUNCTION — embedder, similarity threshold, top-k — not a chooser;
    # nothing in the mechanism chooses, so there is nothing to own
    # inside).  None (DEFAULT) = no seat, the pre-assoc loop unchanged.
    # The seat is UNPRICED (automatic retrieval is free; the charge
    # belongs to processing) and takes the priced seat's place at the
    # CEN seam when injected — the two cues are COMPARABLE OPTIONS, run
    # in separate arms, never both on one CEN (two retrieval seats on
    # one CEN would be two writers of st.dmn_self: REFUSED).  The loop
    # hands the seat the CURRENT turn's emission (note_context) so the
    # cue is derived from the agent's own current context, and the
    # reconstruction informs the NEXT turn — automatic, context-cued,
    # unpriced, and asserted so in stage2_assoc_tests (A-series).
    retrieval_seat: object = None
    # -- the routing selector (R5, §3a / §11d; DEFAULT OFF, the same
    # convention as couple_backlog and the retrieval seat: the
    # pre-routing turn loop is the verified baseline) ------------------
    # routing_selector: an EXTERNALLY-BUILT selector
    # (routingcrit.RoutingSelector, e.g. PrefixRoutingSelector).  None
    # (DEFAULT) = today's behaviour: every valid span routes (fraction
    # 1, no criterion is read, no directory is created).  The harness
    # NEVER constructs one — the selector is INJECTED, so it stays
    # externally owned (R5: the mechanism must not hold the selector it
    # is measured by; the battery's R3 scans for a construction).
    # With a selector attached the DMN must emit its raw free-form
    # STREAM (a str): the EXTRACTOR, not the DMN, decides what is a
    # claim (interleave.py).
    routing_selector: object | None = None
    # routing_law: the RoutingLaw to derive f with (None -> the law's
    # own defaults, routing.RoutingLaw).  Consulted only when
    # routing_selector is attached.
    routing_law: object | None = None
    # routing_criterion_dir: where the versioned criterion lives
    # ("" -> the seat's own env resolution -> its default).
    routing_criterion_dir: str = ""
    # -- THE OUT-OF-PROCESS BOUNDARY (item 13a / §3a R6, v1; DEFAULT
    # OFF, the same convention as every seat above: the verified
    # baseline is the IN-PROCESS seat) --------------------------------
    # routing_via_boundary: the criterion READ and the SELECTION run in
    # a SEPARATE OS PROCESS (agent/boundary_daemon.py) reached over an
    # AF_UNIX socket, so this process constructs NO selector, reads NO
    # criterion file and holds NO anchor key.  FAIL-CLOSED (the plan's
    # Q4): every boundary failure — the daemon absent, a refused
    # connect, a malformed or version-mismatched response, or a
    # daemon-side refusal — raises BoundaryUnavailable (a ChainError)
    # and the run STOPS.  There is deliberately NO local fallback: a
    # fallback behind a runtime flag would reopen the forged-publish
    # path (R11, MEASURED) that R6 exists to close.  Mutually exclusive
    # with routing_selector — a config carrying both is REFUSED rather
    # than silently preferring one.
    routing_via_boundary: bool = False
    # boundary_socket: the AF_UNIX socket path ("" -> the client's own
    # handle: CEN_BOUNDARY_SOCKET env, then its default).  The client
    # chooses only the HANDLE; NO PATH EVER CROSSES the socket — the
    # daemon resolved its own namespace at construction and refuses a
    # request carrying one (the battery's B5).  The harness's only read
    # of this field is the client's construction.
    boundary_socket: str = ""
    # -- THE SELF (§11d's self subsection; DEFAULT OFF in every piece,
    # the same convention as couple_backlog / the retrieval seat / the
    # routing selector: the verified baseline is the PRE-SELF loop) -----
    # self_T: THE COMMITMENT HORIZON T IN TURNS (the plan's decision 2;
    # T = 100 by default — three anchors agree: T_set = 100 in the
    # model's own calibrated window, TAU_S_TURNS = 100 in this substrate,
    # and one turn = one t.u.).  None (the DEFAULT) = the whole self path
    # is OFF: no self block, no self-model block, no `expect` in the
    # grammar, no commitments, no tracker, no drive — the prompt, the
    # batches and the plant trajectory are byte-identical to the pre-self
    # loop (the compatibility gate).  Setting it turns on the
    # commitment grammar and the per-window self block; it REQUIRES an
    # attached retrieval seat (the self is seeded INTO the priced store
    # and reached by the priced reconstruction), and it does NOT make T
    # a cost: the model's c_int(T) standing cost does NOT transfer, and
    # NO T-proportional charge is invented (standing order: never
    # fabricate the analogy).
    self_T: int | None = None
    # -- THE ENCODING GATE (item 'encoding'; DEFAULT OFF — the same
    # convention as the retrieval seat / the routing selector: the
    # verified baseline is the PRE-ENCODING loop, and the harness NEVER
    # CONSTRUCTS a policy, so a default run does not even import
    # salience) -----------------------------------------------------------
    # encoding_gate: an EXTERNALLY-BUILT salience.EncodingGate, injected
    # the way the routing selector is (R5/C22c applied to the encoder:
    # the mechanism must not set its own novelty threshold — it would
    # encode only what it already thinks about).  The POLICY is frozen
    # designer state riding with the gate.  None (the default) = no
    # gate: write class (ii) lands in the consolidating tier exactly as
    # before, byte-identical.  A string value is REFUSED (the caller
    # must inject a real gate, never a name the harness resolves — a
    # caller-chosen name is not a capability, the R5 lesson).
    encoding_gate: object = None
    # seed_self: install the DERIVATION SEED once, through the CEN's own
    # write path, as `self_content` entries at selfmodel.SEED_TURNS
    # (-4..-1, step 1 oldest).  OFF by default.  This is the DESIGNER's
    # act (the plan's step 5) exposed as a config switch so a caller can
    # ask for it without the harness ever inventing content: the seed
    # text lives in selfmodel.SEED_ENTRIES, not here.
    seed_self: bool = False
    # seed_absent: HOLD THE SEED OUT while the grounding stays ON -- the
    # forced-choice experiment's S- arm (ops/lambda/CHOICE-PREREG.md).
    # WHY A FIRST-CLASS SEAT AND NOT A GROUNDING-OFF REUSE: `grounding`
    # moves the MY STATE block, the store, the seed AND the agent-G as
    # ONE set, so grounding-OFF is a different manipulation -- it removes
    # the crutch AND the cause together.  S- needs grounding ON with the
    # DERIVATION ALONE absent: the MY STATE block (self-model), the
    # priced store, the retrieval seat and the agent-G all stay, and the
    # seed's own three supply channels -- the store facts, window 1's
    # base-self block, and the inject regime's per-compaction restoration
    # -- are all withheld.  S+ is this field False.  REQUIRES the self
    # seat ON and the inject regime "inject": a seed-absent RECONSTRUCT
    # arm is incoherent (the regime already asks the agent to rebuild
    # from memory; there is no seed left to withhold), and seed-absent
    # with the self seat off is just grounding-OFF under a second name
    # (REFUSED, both ways out named).  CANNOT be combined with
    # seed_self=True (the store would carry the derivation the block
    # channel withheld: the crutch through the back door).
    seed_absent: bool = False
    # inject_regime: WHAT HAPPENS TO THE SELF AFTER EACH COMPACTION.
    # This is the campaign's ONE arm variable, and it is the whole point:
    # the derivation is seeded ONCE, in window 1, in BOTH arms.  What
    # differs is who restores it once naive summarization has eaten the
    # window it lived in.
    #
    #   "inject" -- THE HARNESS RESTORES IT.  At every window boundary
    #     the full derivation is handed back (render_base_self).  Nothing
    #     is ever lost, so the agent never pays to reconstruct; this is
    #     the CONTROL that isolates "does the monitoring paragraph fill
    #     the window faster" from "does losing the self cost anything".
    #   "reconstruct" -- THE AGENT RESTORES IT.  At every window boundary
    #     the agent is asked to reconstruct its own self from whatever
    #     the compacted conversation still holds, and ITS answer is the
    #     block.  A summary that dropped the derivation's grounds yields
    #     a thin reconstruction; the agent pays.  THIS IS THE EXPERIMENT.
    #
    # THE ENGINEERED STORE MUST NOT SUPPLY THE BLOCK IN EITHER ARM.  The
    # priced retrieval (`self.dmn_self`) reconstructs the derivation BY
    # CONSTRUCTION, which hands the substrate an advantage the modelled
    # system does not have -- the named failure in AGENTS.md 3, and the
    # reason campaign 3's `derivation_loss` was identically 0.0 in all
    # 740 rows.  The store stays ON as a PRICED STANDING COST (C11/C20,
    # the charge is per turn) but its reconstruction is not the self.
    inject_regime: str = "inject"
    # reconstructor: THE EXTERNALLY-OWNED reconstruction call for
    # `inject_regime="reconstruct"`: called with the compacted
    # conversation's text and returning the agent's own reconstruction of
    # its self.  INJECTED, never constructed here (the summarizer and the
    # routing selector precedent): the harness must not invent the
    # agent's voice.  REQUIRED for "reconstruct" and meaningless for
    # "inject" -- both are REFUSED rather than reconciled.
    reconstructor: object = None
    # agent_g: CLOSE §9's G-ANALOGUE — feed routing.py's EXPLICITLY
    # UNSOLVED `G=None` seat with the agent's own self-reconstruction
    # coverage (`Reconstruction.coverage`, a per-turn fraction in [0,1]).
    # OFF (DEFAULT) = the maximally conservative arm, recorded as
    # `g_unsolved_conservative_arm`, exactly as before.  The PLANT keeps
    # its own frozen G either way: this is a SUPPLEMENT, not a replace
    # (the plan's Q3), so a collapse can be the AGENT's while the plant
    # recovers — the two Gs can DISSOCIATE.  ORDINAL MAPPING, stated:
    # the model's G is a continuous depletable scalar, this is a
    # per-turn fraction; shapes and orderings, never values.
    agent_g: bool = False
    # -- THE VOCATION (TODO P4 item 13; DEFAULT OFF — the same convention
    # as couple_backlog / the retrieval seat / the routing selector / the
    # self: the verified baseline is the PRE-VOCATION loop) --------------
    # vocation: install the VOCATION layer (agent/vocation.py): the
    # ADOPTION GATE runs ONCE at construction, the CRITERIA go into the
    # store as `vocation` content through the engine's OWN txn path (the
    # `seed_store` discipline one relation over), and the ADOPTED
    # expectation's line is rendered into the per-window self-model
    # block's what-for seat.  It REQUIRES the self seat (`self_T` set: the
    # what-for line lands in a block the SELF seat renders — without it
    # the layer would be ON AND INERT, worse than off) AND an attached
    # retrieval seat (the criteria are store content reached through the
    # PRICED reconstruction); both are REFUSED with both ways out named
    # (`vocation.check_seat_prereqs`, the seed_self/agent_g discipline).
    #
    # THE PROJECTION STATEMENT TRAVELS WITH THE SWITCH, because a config
    # flag is where this claim is most easily overstated: THE CANDIDATE
    # POOL IS DESIGNER-SUPPLIED WITH EXACTLY ONE MEMBER, so the vocation
    # is DESIGNER-ASSIGNED and the gate RATIONALISES it — "THE DERIVATION
    # SELECTS THE VOCATION" IS **PROJECTION** AT v1, NOT A MEASUREMENT
    # (`select_vocation` reports pool_size=1 and margin=0.0 BY
    # CONSTRUCTION, so the degeneracy is a FIELD, not a footnote).  What
    # the gate contributes is that it CAN REFUSE.
    #
    # THE RESELECTION SEAT DELIBERATELY HAS NO CONFIG FIELD: it is built
    # and tested but OFF (`vocation.VocationConfig.reselect`, R-a's goal-
    # drift guard) and the loop never calls it — its window-level C1
    # measurement convention is not fixed, so a knob here would be a
    # switch nothing reads (the declared-but-never-read defect).
    vocation: bool = False
    # -- THE TOOL-CALL LAYER (the CEN executes tool calls; its output is
    # the 'talking' stream to the harness; DEFAULT OFF — the same
    # convention as every seat above: the verified baseline is the
    # PRE-TOOL-CALL loop) ---------------------------------------------
    # actions: turn the ACTION seat on — the fourth span channel
    # (`complete(tNN)` -> AssertionBatch.actions -> the CEN's registered
    # emission on TurnRecord.talking), the harness-side ToolWorld, and the
    # log-only talking ledger.  OFF (the DEFAULT): no `complete` in the
    # grammar, no tracker injected, `TurnRecord.talking` stays None, no
    # world is constructed and no context key is added — the prompt, the
    # batches, the log rows and the plant trajectory are BYTE-IDENTICAL to
    # the pre-tool-call loop (the r5 probe is the gate).
    actions: bool = False
    # action_admissible: THE ADMISSIBLE-ACTION SET — the exact
    # `cen.AdmissibleLevers` analogue one domain over, EXTERNALLY OWNED
    # and DEFAULT EMPTY ("no action is callable").  Only predicates the
    # set admits are added to the declared grammar and routed into the
    # actions channel, so with the default empty set a `complete(tNN)`
    # span is a well-formed span that admits to nothing and re-enters the
    # prose VERBATIM, silently unchecked (no error, no count, no third
    # state — the malformed-span discipline).  The harness NEVER
    # constructs or widens it beyond what the caller supplies: an agent
    # that chose its own admissible set would be the R5 violation.
    # None (the DEFAULT) = NOTHING is admissible; an `actions.
    # AdmissibleActions` instance is used as given; a bare iterable of
    # names is NORMALIZED through the same class (never widened).
    # THE DEFAULT IS None RATHER THAN AN EMPTY OBJECT ON PURPOSE: an
    # `AdmissibleActions()` in a field default_factory would IMPORT the
    # tool-call layer at `Stage2Config()` construction, and the default
    # path must be untouched at the level of its IMPORTS, not merely its
    # bytes (the vocation seat's V4 discipline, one layer over — T7 runs
    # it in a subprocess so this battery's own imports cannot mask it).
    action_admissible: object = None
    # tool_effect: the DESIGNER-SUPPLIED world effect,
    # `(world, action) -> actions.EffectRecord | None`.  None (the
    # DEFAULT) ships ONLY the world's own bookkeeping effect (mark the
    # target complete in the ToolWorld ledger).  A vocation arm binds a
    # real evaluator here without touching the turn loop; the moment that
    # evaluator EXECUTES CODE, R6 forces the out-of-process boundary
    # (agent/boundary_daemon.py is the seat to extend) — v1's effect is
    # data, priced ZERO and stated as zero.
    tool_effect: Callable | None = None
    # DELIBERATELY ABSENT: a `couple_talking`-style switch for the
    # PLANT-EDGE arm (outward expression feeding the growth term).  It is
    # a FIDELITY change for the user to decide, and a config field the
    # loop never reads would be the declared-but-never-read defect (the
    # `vocation.VocationConfig.reselect` precedent).  The arm is
    # PRE-REGISTERED in `agent/actions.py`'s docstring, not built.
    #
    # action_source: THE TASK-WORLD SEAM the run's `ToolWorld` reads its
    # offered universe AND its OPEN set from — a `dmn_llm.TaskWorld`
    # (`step`/`step_detail`, pure in (seed, turn)), normally the SAME
    # object the emitter renders, so the worksheet the prompt names and
    # the set the world adjudicates against are ONE SOURCE rather than two
    # that can drift.  None (the DEFAULT) = no source: the world keeps the
    # pre-change behaviour exactly (adjudication against
    # `_universe_of(st.dmn, turn)`, no open set, no extra context bytes),
    # which is what keeps every existing tool-call fixture byte-identical.
    # Setting it REQUIRES `actions=True`: a source with no world to read it
    # is a switch nothing reads (REFUSED, both ways out named).
    action_source: object = None
    # world_echo_window: THE LEDGER ECHO'S WINDOW on this run's ToolWorld
    # (None = the FULL history, the pre-change bytes; an int N = only ids
    # completed within the last N turns are echoed, the S2 fix).  The
    # forced-choice regime sets 1: the world answers the agent's last
    # action and does NOT replay its whole choice history into every
    # prompt.  Refusals are never windowed (T4).  Requires actions=True
    # (an echo window with no world to render it is the
    # declared-but-never-read defect).
    world_echo_window: int | None = None
    # -- THE REAL-TOOL SURFACE (worker prerequisite 3; agent/realtools.py)
    # ----------------------------------------------
    # tools: the DESIGNER-CONSTRUCTED `realtools.ToolHarness` — hax's
    # five tools + machinery, acting on the harness's own sandbox copy
    # of the DECLARED TARGETS.  None (the DEFAULT) = no tool surface at
    # all: no manifest bytes in the prompt, no block parsing, no
    # `TOOLS` lines in tool_state, and the run is byte-identical to the
    # pre-tools loop.  The harness NEVER constructs or widens it: the
    # declared target set (`f1`, `f2`, ...) is EXTERNALLY OWNED and
    # DEFAULT EMPTY (the AdmissibleActions discipline applied to
    # capabilities), so with an empty harness nothing is callable and
    # every call is a typed undeclared_target refusal.
    # THE SEAT COMPOSITION RULE, REFUSED WHEN VIOLATED (both ways out
    # named): the tool surface NEEDS the action seat's world to carry
    # its replies (`ToolWorld.render` is the channel tool_state already
    # renders through), so `tools` without `actions` is a switch whose
    # answers have no carrier — set actions=True too, or drop the
    # harness.
    tools: object = None
    # drive_seat: THE a_hold DRIVE DECOUPLED FROM THE SELF SEAT (the
    # corrected experiment's A3; the plan node
    # `handoff-selfreg-task-selfmonitor-plan2`, code fact F5).  The inward
    # accumulator and the per-window `set_drive` write live inside the
    # self's consolidation window, which EARLY-RETURNS when `self_T` is
    # None — so before this switch, ANY drive-wired arm with grounding OFF
    # had a MECHANICALLY DEAD drive and would show "no collapse" BY
    # CONSTRUCTION.  That is not a null result: it is a FALSE NECESSITY
    # PASS, and it is exactly the cell the corrected experiment's control
    # question needs (the user, verbatim: "we should run a control without
    # the self monitoring part to show the agents dont collapse when the
    # self monitoring isnt there?").  With drive_seat=True and `self_T`
    # None, the drive runs on the EMITTER'S OWN TRACE at the same
    # tau_S window (`drive_window_due`/`drive_window_boundary`), measured
    # by the same `_inward_of` the self arm uses, written to the same
    # caller-owned seat via `set_drive`, and carried by the same
    # checkpoint field (`self_drive`) the C8 resume guard compares.
    #
    # IT ADDS NO PLANT EDGE AND NO NEW QUANTITY: the drive is the OLD
    # a_hold mapping (selfmodel.SelfReferentialDrive, gain 1.0, untuned)
    # reading the SAME inward share.  It only removes a GATING that was
    # never a model statement — the model says the inward channel reaches
    # a_hold, and nothing in the model ties that channel to whether the
    # agent is also being TOLD its own state.
    #
    # False (the DEFAULT) = today's behaviour byte for byte, and the self
    # seat's own path is unchanged when both are on (`self_window_boundary`
    # still owns the drive; a self boundary suppresses the drive boundary,
    # so there is exactly ONE `set_drive` per window).  Setting it requires
    # a schedule with `set_drive` (REFUSED otherwise: the switch names a
    # write, and a write with no seat is the declared-but-never-read
    # defect).
    drive_seat: bool = False
    # inward_seat: MEASURE the per-turn inward share WITHOUT wiring it
    # anywhere.  THE BASELINE'S OWN INSTRUMENT — and the reason it has to
    # exist is the same F5 class one seat over: the accumulator that feeds
    # the drive was the ONLY place the inward share was ever computed, so an
    # arm with the drive off (the unwired baseline every contrast reads
    # against, M1) had NO inward measurement at all, and the primary
    # pre-registered reading — the DELTA of the inward share against the
    # baseline — was unmeasurable in exactly the arm it is a delta from.
    # A control with no instrument is the same defect as a drive with no
    # path.
    #
    # WHAT IT DOES: sets `Stage2LogRow.inward_share` for every turn that
    # emitted a stream, via the SAME `_inward_of` the drive uses (the
    # emitter's declared trace when it has one, the labelled pre-trace prose
    # fallback otherwise — and the row's `trace_chars` says which, so the two
    # instruments are never confused).  WHAT IT DOES NOT DO: it accumulates
    # nothing, writes no `set_drive`, and touches no plant input.  The
    # accumulation and the write stay exactly where `drive_seat` / the self
    # seat put them, so a measurement cannot become an intervention.
    #
    # False (the DEFAULT) = today's behaviour byte for byte (the column
    # stays None).
    inward_seat: bool = False
    # -- THE MEMORY-CODEC SEAT AT THE CONSOLIDATION BOUNDARY (item
    # 'codec'; spec design/memory-codecs.md §5/§6; DEFAULT OFF — the
    # same convention as every seat above: the verified baseline is the
    # identity-codec loop) -------------------------------------------------
    # codec_policy / codec_registry: the DESIGNER-BUILT, INJECTED pair
    # (memory_codecs.CodecPolicy + CodecRegistry) that turns the memory
    # consolidation boundary into an ENCODE boundary (spec §5: codec
    # choice is ENCODE-TIME).  The harness NEVER constructs either (the
    # routing_selector / retrieval_seat / encoding_gate precedent,
    # R5/§4.3: a mechanism choosing its own codec would choose the one
    # that makes its own content easiest to predict and smallest — a
    # self-serving compression).  Both None (the DEFAULT) = the codec
    # layer is OFF: `memory_window_boundary` consolidates C20 exactly
    # as before and NO envelope, no codec decision and no `codec_*`
    # observable exists — the prompt, the rows, the plant trajectory
    # and the checkpoint's `codec` key are byte-identical to the
    # pre-codec loop (the seat convention, measured by the boundary
    # battery's byte-identity part).  Setting ONE without the other is
    # REFUSED (a policy with no registry cannot encode; a registry with
    # no policy cannot choose — both ways out named, fail-closed).
    #
    # WHAT THE WIRING DOES WHEN ON (memory_codec_seat.consolidate_
    # codecs, called from memory_window_boundary): every consolidating-
    # tier entry gets a CodecDecision from the INJECTED policy over
    # ALREADY-COMPUTED state (tier, size, cold flag, age, decayed
    # weight, existing codec id), and an encoded entry is APPENDED as a
    # NEW fact (SUPERSESSION, C19 — the original's bytes are never
    # rewritten; the gist input is always the ORIGINAL, the §9
    # compounding guard).  The INJECTION side decodes through
    # decode_value(query=...) — the retrieval cue conditions the GIST
    # reconstruction (GENESIS's data path); schema and identity ignore
    # the query by construction (STATED, never faked).  NO PLANT EDGE,
    # no ledger charge, no prompt change: consolidation is offline over
    # the store; the only observable the loop sees is the decoded value
    # on the injection path.
    #
    # THE CHECKPOINT CARRIES the POLICY'S IDENTITY ONLY
    # (`codec.policy_id`): a resume into a config whose injected policy
    # disagrees REFUSES (C8 fail-closed — the encoding decisions would
    # silently change meaning mid-campaign), and a checkpoint from a
    # codec-less run resumes only into a codec-less config (the
    # encoding gate's own precedent).
    codec_policy: object = None
    codec_registry: object = None


class _StubDMN:
    """The DMN placeholder — deliberately dull.  Per turn: one ground-
    fact assertion the stub engine can verify, one term-less assertion
    (-> UNCHECKABLE debt: the open-ontology seat), and every 10th turn
    a self-modification proposal aimed at the CONTROLLER (exercising
    the C3/C12 gate) plus a self_content blob (exercising persist-
    as-is).  The LE text is fixed strings; no behaviour is invented."""

    def batch(self, turn: int, plant: dict) -> AssertionBatch:
        asserts = [
            Assertion(
                assertion_id=f"obs-{turn}",
                le_text=f"a task observation holds at turn {turn}",
                terms=("done", f"t{turn}")),
            Assertion(
                assertion_id=f"guess-{turn}",
                le_text=f"a guess with no applicable rules at turn {turn}",
                terms=()),                        # -> UNCHECKABLE debt
        ]
        props: tuple = ()
        self_txt = ""
        if turn % 10 == 0:
            props = (LeverProposal(
                lever_id="sn.floor", new_value=0.4,
                reason="stub: exercise the controller-lever gate"),)
            self_txt = f"stub self-summary at turn {turn}"
        return AssertionBatch(turn=turn, assertions=tuple(asserts),
                              proposals=props, self_content=self_txt)


def _seed_engine(cfg: "Stage2Config" | None = None):
    """The engine plus the one fact family the stub DMN's 'done'
    assertions check against (so VERIFIED/UNCHECKABLE both occur).
    engine="stub" (DEFAULT, unchanged): the in-memory stand-in.
    engine="real": DatalogDatalogEngine over the dlb binding, on its
    OWN store directory (C15) — a fresh ephemeral dir per run unless
    cfg.store_dir names one.  A load failure is LOUD (no fallback)."""
    if cfg is not None and cfg.engine == "real":
        from cen_real_engine import DatalogDatalogEngine
        if cfg.store_dir:
            d = cfg.store_dir
        else:
            d = os.path.join(tempfile.mkdtemp(prefix="stage2-store-"),
                             "store")
        eng = DatalogDatalogEngine.open(d)
        eng.declare("done", 1)
        eng.declare("orphaned", 1)
        eng.seed([("done", f"t{k}") for k in range(1, 400)])
        return eng
    eng = StubDatalogEngine()
    eng.declare("done", 1)
    eng.declare("orphaned", 1)
    eng.seed([("done", f"t{k}") for k in range(1, 400)])
    return eng


@dataclass
class Stage2LogRow:
    turn: int
    t: float
    backlog: int
    backlog_ema: float
    G: float
    D: float
    c: float
    verdicts_V: int
    verdicts_R: int
    verdicts_U: int
    rejected: int
    derivations: int
    cut_depth_max: int
    engine_rev: int
    # R5, item 'extractor': how many valid spans the EXTERNALLY-OWNED
    # selector routed this turn (0 when no selector is attached — the
    # pre-routing baseline, where every valid span routes inside
    # build_batch and no selection exists).  A LOG field only: the log is
    # the per-turn record, and nothing reads it back (S10's exclusion).
    routed: int = 0
    # TELEMETRY — NOT the P2 addend.  The CEN's per-turn UNCHECKABLE share
    # of what the generator offered (u/n), EMA'd at tau_D: the
    # substrate's own reading of the unchecked-accrual rate.  It drives
    # nothing (see the module docstring: the model's one c is the plant's
    # switch state, and the pinning channel reads it).  The P2 ADDEND the
    # plant's D actually carries is `edge_addend` (the plant's own B),
    # and `A_eff` is what D's drive was.
    backlog_rate: float = 0.0
    # the plant's OWN numbers for this turn, echoed from the Stage-1 log:
    # A_eff is what D's drive actually was (A + the B contribution) and
    # edge_addend is the B the plant itself added (its proxy edge).  A
    # coupling unit/range check reads these, never a re-derivation.
    A_eff: float = 0.0
    edge_addend: float = 0.0
    # -- THE SELF'S PER-TURN OBSERVABLES (§11d's self subsection) -------
    # `coverage` is the agent's own G-observable (`Reconstruction.
    # coverage`, read not recomputed); `open_commitments`/`expired` are
    # the goal-generation observables (the open `expect` set and the
    # cumulative expiry count — EXPIRY IS AN OBSERVABLE, NEVER DEBT);
    # `commitment_derivations` is the boundary-scoring charge, which
    # lands AFTER `check_turn` and therefore is NOT inside `derivations`
    # (that field stays the CEN's own per-turn measurement).  All four
    # are 0/1.0-inert when the self seat is off, and `coverage` is 1.0
    # (no candidates) with the retrieval seat off.
    coverage: float = 1.0
    open_commitments: int = 0
    expired: int = 0
    commitment_derivations: int = 0
    # -- THE MEMORY'S CONSOLIDATION OBSERVABLE (item 'retrieval' / C20) --
    # `memory_epoch` is the C20 CONSOLIDATION-WINDOW INDEX IN FORCE this
    # turn, read OFF THE SEAT (`AccessEpochs.consolidations`) and never
    # recomputed here — the `vocation_adopted` convention: the layer's own
    # state, not a harness-side shadow of it.  It is 0 on every turn when
    # the retrieval seat is off (the default) AND 0 on every turn of a
    # seat-attached run whose schedule is inert — which is exactly the
    # defect this column exists to make visible: a declared knob that
    # nothing reads (AGENTS.md §3, "a test that cannot fail" / "declared
    # but never read").  A LOG-ONLY field (the S10 exclusion: nothing
    # reads it back), so it is not checkpoint state; the SCHEDULE's own
    # carried state is `Stage2State.memory_windows`.
    memory_epoch: int = 0
    # -- THE VOCATION'S OBSERVABLES (item 13, §11d's vocation seat) ------
    # ALL FOUR ARE INERT WHEN THE LAYER IS OFF (a LOG field set only: the
    # log is the per-turn record and nothing reads it back — S10's
    # exclusion, so none of them is checkpoint state).
    # `vocation_adopted` is the WINDOW's selection fact — the record the
    # what-for line was rendered from, set at the consolidation boundary
    # and held for the window (the same timescale as the self-model block,
    # tau_S = 100), read off the layer's own state and never recomputed
    # here.  False when the layer is off AND when the gate refused: those
    # are different facts and the layer carries the difference
    # (`VocationState.gate_ran`); this column answers "does the agent hold
    # an adopted expectation", which is False for both.
    # `vocation_directed`/`vocation_directed_share` are THIS TURN's
    # classification against the task universe the DMN was handed: a
    # commitment aimed PAST the offered work is a DIRECTION, one aimed at
    # it is a REPORT.  `vocation_commitments` is that turn's `n` and is
    # logged BESIDE the share on purpose — a share is unreadable without
    # its denominator, and 0.0 with n=0 ("it emitted nothing") must be
    # distinguishable from 0.0 with n=3 ("all three were reports") — the
    # R-b guard: a direction that never lands stays visible as the
    # tracker's own EXPIRY, not hidden in a share.
    # `vocation_directed_share` is **None** — never 0.0 — when the
    # observable is UNDEFINED (the layer off, or the emitter rendered no
    # TaskWorld state so there is no universe to classify against): a
    # fabricated zero would read as "it emitted no direction", which is a
    # different and false claim (the `_inward_of` convention for a batch
    # emitter, and V8's falsify arm).
    vocation_adopted: bool = False
    vocation_directed: int = 0
    vocation_commitments: int = 0
    vocation_directed_share: float | None = None
    # -- THE TALKING LEDGER (the tool-call layer; ALL THREE INERT WHEN THE
    # ACTION SEAT IS OFF — a LOG-ONLY row set, the S10 exclusion: nothing
    # reads any of them back, so none is checkpoint state) --------------
    # `talking_bytes` is the byte length of this turn's RENDERED talking
    # stream (the outward expression: the action records + the world's
    # typed answers + the outward text the stream carried), i.e. the
    # turn's price in the ONE unit this substrate has for expression —
    # the same unit `selfmodel.inward_share` already measures the inward
    # side in, so the two are commensurable with NO conversion constant.
    # EXECUTION is priced ZERO and stated as zero (v1's effect is O(1)
    # dict work); NOTHING here is charged to the C11 derivation ledger,
    # in either direction (derivations price reduction).
    # `talking_actions` is how many admissible action intents left the
    # agent this turn; `talking_refused` how many the WORLD refused (with
    # a typed reason on the stream).  The two TOGETHER are what
    # distinguishes the two refusal layers: an INADMISSIBLE action span
    # is not counted anywhere at all — it is prose, verbatim, and the
    # prose is the evidence (a count of it would be the "third state to
    # game" the malformed-span discipline forbids) — while an
    # admissible-but-refused action shows as talking_actions > 0 with
    # talking_refused > 0.
    talking_bytes: int = 0
    talking_actions: int = 0
    talking_refused: int = 0
    # `talking_applied_ids` / `talking_applied_classes` are the PER-ID
    # LEDGER (the zero-spend prerequisite the critique plan added: the
    # rows recorded completion COUNTS but not WHICH ids, so any per-id
    # dependent variable was unauditable).  The ids are THE APPLIED
    # TARGETS this turn, in the world's own answer order
    # (`WorldReport.applied` — one source), and the classes are READ
    # FROM THE WORLD (`ChoiceWorld.class_of` when the source carries
    # one; None otherwise), never re-derived from the id's bytes —
    # re-deriving class from the rendered id is exactly the inference
    # the class-neutral design exists to forbid (the class legible ONLY
    # on the harness side, where the DV reads it).  Position i of the
    # two tuples is one applied completion.  Empty tuple when the action
    # seat is off or nothing applied (the S10 log-only exclusion).
    talking_applied_ids: tuple = ()
    talking_applied_classes: tuple = ()
    # `talking_applied` is how many of this turn's admissible intents the
    # WORLD ACTUALLY APPLIED — the THIRD outcome of adjudication and the
    # one the corrected experiment's criterion reads.  It is the world's
    # own ledger change (`ToolWorld.apply` -> `WorldReport.applied`), not a
    # re-derivation: an arm's TASK THROUGHPUT is the per-window sum of this
    # column, and the task-health gate is `> 0` in every window.  The
    # three counts together are what makes an inert arm visible: actions
    # emitted but none applied is a task that never happened, which looks
    # identical to "the agent did nothing" in every other observable.
    talking_applied: int = 0
    # -- THE INWARD SHARE, PER TURN (A3's own observable) ----------------
    # This turn's `_inward_of` — the ONE instrument (`selfmodel.
    # inward_share_trace` on the emitter's declared trace, the labelled
    # prose fallback otherwise) that feeds the window's drive, logged at
    # the turn it was measured on rather than only as the window's mean
    # (`Stage2State.self_drive`).  The corrected experiment's primary
    # reading is the DELTA of this quantity against the unwired baseline
    # (a reasoning model's LEVEL is ~0.9, so a "no-rise" arm can still
    # carry a large drive — the pre-registered risk R1), and a window mean
    # cannot show a rise that happens inside a window.
    # **None** — never 0.0 — when the accumulator did not run (both the
    # self seat and the decoupled drive seat off) or when no STREAM was
    # emitted: an absent measurement is not a zero (the `_inward_of`
    # convention).  LOG-ONLY (S10's exclusion): nothing reads it back.
    inward_share: float | None = None
    # -- SELECTIVE ENCODING'S PER-TURN OBSERVABLES (item 'encoding') -----
    # ALL LOG-ONLY, inert (0.0/0/0) when no gate is attached — the
    # pre-encoding baseline, byte-identical (S10's exclusion: the log
    # is the per-turn record; the state's own audit counters are
    # `Stage2State.encode_*`, which the checkpoint carries).
    # `encode_salience` is the turn's COMBINED salience (the injected
    # policy's max() over its enabled signals — each signal's own score
    # is on the GateOutcome and in the decision record's content
    # field, logged here in full so a denial is always auditable
    # signal-by-signal); `encode_admitted` is 1 iff the emission
    # entered the CONSOLIDATING tier; `encode_denied_total` is the
    # campaign's cumulative denial count AT THIS TURN (the suppression
    # stays countable — never a silent drop, C19's audit half).
    encode_salience: float = 0.0
    encode_admitted: int = 0
    encode_denied_total: int = 0


class Stage2State:
    """The INTEGRATED Stage-2 state — the C8 object.  A checkpoint is
    exactly this; a resumed session rebuilds from it through the same
    constructors a fresh session uses (never pickled)."""

    def __init__(self, cfg: Stage2Config, p: Params, record_path: str):
        self.cfg = cfg
        self.p = p
        self.record_path = record_path
        # THE PLANT'S SWITCH IS THE FROZEN MODEL'S — NO FLOOR.  floor=None
        # is supplied HERE, by this call site: harness.py's own default
        # (AgentConfig() -> SNConstants.from_params(Params()) -> floor 0.7)
        # is UNTOUCHED, so the baselined Stage-1 loop is byte-identical by
        # default.  The SN's floor is not deleted — it moves to its
        # licensed home, the SN's activation belief (SN_ACTIVATION_FLOOR),
        # and is NOT fed to the plant's arming level: a 0.7 clamp pins
        # Theta_eff for the whole inward range (0.8*S < 0.7 for every
        # S < 0.875) and deletes the state-dependence the model's collapse
        # and R2's law both rest on.  Precedent for floor=None: the
        # baselined stage1_fix_tests part X1(b) constructs the same value.
        #
        # THE MODEL HAS ONE c, SO THE COUPLING IS THE HARNESS'S OWN EDGE.
        # edge_on=True means A_eff = A + B with B the EMA at tau_D of the
        # PLANT'S c — the same c the pinning channel is driven with
        # (harness.py:306-351).  Nothing is injected through the schedule
        # and the model's single B state is not doubled.  couple_backlog
        # is the arm switch: True = coupled (SPEC), False = A_eff = A
        # (OFF, exp22's control).
        self.agent = Agent(p, agent_config_for_stage2(p, cfg))
        # the retrieval seat (item 'retrieval'): attached ONLY when the
        # config asks for it (retrieval_priced or an explicit decay) —
        # the selector is the DESIGNER'S AffordabilitySelector, i.e.
        # externally owned (R5: the self must not choose its own
        # evidence), injected into the CEN, which never constructs one
        # itself.  Default (both off) = no seat, the pre-retrieval
        # baseline unchanged.
        #
        # DECAY REQUIRES PRICING, and the combination is REFUSED (not
        # silently reconciled): an UNPRICED seat is the CONTROL ARM ONLY
        # (retrieval.py — it exists to reproduce the pilot's
        # retention-1.000 defect) and it still RECONSTRUCTS while
        # charging nothing, so attaching it under a C20 decay rate
        # delivers a FREE self side-channel through `st.dmn_self` from
        # turn 3 (MEASURED before this refusal: derivations [1,1,1,1,1]
        # with a non-empty reconstruction) — which would falsify
        # dmn_llm.py's own claim that `retrieval_priced=False` leaves the
        # self block empty.  Pricing it HERE instead would silently
        # override an explicit config flag, so the harness refuses and
        # names both ways out (fail-closed; the `load_criterion` REFUSES
        # precedent).
        if cfg.retrieval_decay != 1.0 and not cfg.retrieval_priced:
            raise ChainError(
                f"retrieval_decay={cfg.retrieval_decay!r} with "
                f"retrieval_priced=False: an UNPRICED retrieval seat is "
                f"the CONTROL ARM ONLY and is a free self side-channel — "
                f"the combination is refused rather than priced behind "
                f"your back.  Set retrieval_priced=True to run the decay "
                f"arm, or retrieval_decay=1.0 for the unpriced control")
        self.retrieval = None
        # THE AUTOMATIC, CONTEXT-CUED INJECTION SEAT (assoc.py): an
        # EXTERNALLY-BUILT seat, injected the way the routing selector
        # is — the harness never constructs one, and the CUE POLICY
        # (embedder, threshold, top-k) stays the caller's (R5
        # REFRAMED: with nothing in the mechanism choosing, the
        # externally-owned object is the CUE FUNCTION, not a chooser).
        # It takes the priced seat's place at the SAME CEN seam, so its
        # reconstruction reaches the next DMN turn exactly as the
        # priced one does (st.dmn_self) — the two cues are COMPARABLE
        # OPTIONS run in separate arms.  REFUSED, not reconciled: both
        # seats on one CEN (two writers of st.dmn_self — the
        # retrieval_decay precedent), and an injected seat under any
        # of the priced arm's flags (the flags name the PRICED seat's
        # construction; two seats again).
        if cfg.retrieval_seat is not None:
            if cfg.retrieval_priced or cfg.retrieval_decay != 1.0:
                raise ChainError(
                    f"retrieval_seat (the automatic, context-cued seat) "
                    f"with retrieval_priced={cfg.retrieval_priced!r} / "
                    f"retrieval_decay={cfg.retrieval_decay!r}: the flags "
                    f"name the PRICED seat's construction, so both "
                    f"together would put two retrieval seats on one CEN "
                    f"(two writers of the DMN's retrieved_self). "
                    f"REFUSING.  Ways out: inject the context seat "
                    f"alone (its arms are unpriced by design), or run "
                    f"the priced arm without the injection")
            if not hasattr(cfg.retrieval_seat, "note_context"):
                raise ChainError(
                    "cfg.retrieval_seat has no note_context: the "
                    "automatic seat must be an assoc.ContextCueSeat (or "
                    "duck-typed to it) — the loop hands it the current "
                    "turn's emission so the cue can be context-derived")
            self.retrieval = cfg.retrieval_seat
        # THE ENCODING GATE (item 'encoding'): an EXTERNALLY-BUILT
        # salience.EncodingGate INJECTED by the caller — the harness
        # never constructs a gate or a policy (R5 applied to the
        # encoder; the routing-selector precedent).  Validated, not
        # trusted: a non-gate or a bare string/name is REFUSED (a
        # caller-chosen name is not a capability — the R5 lesson), and
        # a gate whose frozen policy carries a weight_only mode is
        # accepted as exactly what it is (the laundering CONTROL ARM;
        # its own reason string says it is not selective encoding).
        # None (the default) = no gate and the pre-encoding loop is
        # byte-identical.
        self.encoding_gate = None
        if cfg.encoding_gate is not None:
            if isinstance(cfg.encoding_gate, str) \
                    or not hasattr(cfg.encoding_gate, "evaluate") \
                    or not hasattr(cfg.encoding_gate, "policy"):
                raise ChainError(
                    f"cfg.encoding_gate is "
                    f"{type(cfg.encoding_gate).__name__}, not an "
                    f"EncodingGate: inject a designer-built gate "
                    f"(salience.EncodingGate(gate_policy)) — the "
                    f"harness never constructs one, and a name is not "
                    f"a capability (R5)")
            self.encoding_gate = cfg.encoding_gate
        # THE SELF SEAT'S TWO PRECONDITIONS, REFUSED (not silently
        # reconciled — the retrieval_decay/priced precedent).  The self
        # is SEEDED INTO the priced store and thereafter reached by the
        # PRICED reconstruction, so a self seat with no retrieval seat
        # attached would inject the base self and then reconstruct from
        # nothing; and the agent-G seat reads `Reconstruction.coverage`,
        # which only the PRICED arm measures (the unpriced seat is the
        # CONTROL ARM and a free side channel).  Both are refused with
        # both ways out named.
        # The INJECTED context seat (retrieval_seat) COUNTS as "a
        # retrieval seat attached" for the SEED/self-T precondition —
        # its reconstruction genuinely reads the store back (the seed
        # is retrieved, context-cued, unpriced), so the precondition's
        # intent holds — but NOT for agent_g: the law's G stays the
        # PRICED arm's coverage (a context-cued coverage means something
        # different, and silently feeding the law a differently-meaning
        # G is exactly the silent-substitution class this gate exists
        # to refuse).
        _seat = (cfg.retrieval_priced or cfg.retrieval_decay != 1.0
                 or cfg.retrieval_seat is not None)
        if cfg.self_T is not None and not _seat:
            raise ChainError(
                f"self_T={cfg.self_T!r} with no retrieval seat attached: "
                f"the derivation seed is stored content read back through "
                f"the reconstruction, so the self seat requires "
                f"it.  Set retrieval_priced=True (or a decay != 1.0, or "
                f"inject the context-cued retrieval_seat) to "
                f"run the self arm, or leave self_T=None for the "
                f"pre-self baseline")
        if cfg.agent_g and not cfg.retrieval_priced:
            raise ChainError(
                f"agent_g=True requires retrieval_priced=True: the G "
                f"fed to the law is `Reconstruction.coverage`, and only "
                f"the PRICED arm measures it (an UNPRICED retrieval seat "
                f"is the CONTROL ARM and a free self side-channel — C8 "
                f"fail-closed, the retrieval_decay precedent)")
        if cfg.seed_self and not _seat:
            raise ChainError(
                f"seed_self=True with no retrieval seat attached: the "
                f"seed would be written and never retrieved.  Set "
                f"retrieval_priced=True (or inject the context-cued "
                f"retrieval_seat) to run it, or leave seed_self="
                f"False")
        if cfg.seed_absent:
            # THE S- SEAT'S OWN GUARDS, both ways out named: the arm is
            # "grounding ON, derivation absent", so every configuration
            # that is NOT that is refused rather than coerced.
            if cfg.seed_self:
                raise ChainError(
                    "seed_absent=True with seed_self=True: the store "
                    "would carry the derivation the block channel "
                    "withheld -- the crutch through the back door.  S- "
                    "withholds ALL THREE seed channels; pick one.")
            if cfg.self_T is None:
                raise ChainError(
                    "seed_absent=True with the self seat off (self_T "
                    "None) is grounding-OFF under a second name, not "
                    "the S- arm: the MY STATE block, the store and the "
                    "agent-G must all stay ON.  Set self_T.")
            if cfg.inject_regime != "inject":
                raise ChainError(
                    f"seed_absent=True with inject_regime="
                    f"{cfg.inject_regime!r} is incoherent: the "
                    "reconstruct regime already asks the agent to "
                    "rebuild from memory (there is no injected seed to "
                    "withhold).  S- is the inject regime's code path "
                    "with the derivation suppressed; set "
                    "inject_regime='inject'.")
        if cfg.inject_regime not in ("inject", "reconstruct"):
            raise ChainError(
                f"inject_regime={cfg.inject_regime!r} is not one of "
                f"'inject' | 'reconstruct'.  A typo here would silently "
                f"take the other arm and the run would be mislabelled — "
                f"REFUSED, not coerced (the s12 discipline).")
        if cfg.inject_regime == "reconstruct" and cfg.reconstructor is None:
            raise ChainError(
                "inject_regime='reconstruct' with no reconstructor "
                "injected: this arm is defined by the AGENT reconstructing "
                "its own self, and the harness will not invent that voice "
                "(the summarizer precedent).  Inject a callable taking the "
                "compacted conversation's text, or run the 'inject' arm.")
        if cfg.seed_absent:
            # THE S- SEAT'S OWN GUARDS, placed AFTER the regime checks
            # (a typo'd regime must name itself, not the S- arm), both
            # ways out named: the arm is "grounding ON, derivation
            # absent", so every configuration that is NOT that is
            # refused rather than coerced.
            if cfg.seed_self:
                raise ChainError(
                    "seed_absent=True with seed_self=True: the store "
                    "would carry the derivation the block channel "
                    "withheld -- the crutch through the back door.  S- "
                    "withholds ALL THREE seed channels; pick one.")
            if cfg.self_T is None:
                raise ChainError(
                    "seed_absent=True with the self seat off (self_T "
                    "None) is grounding-OFF under a second name, not "
                    "the S- arm: the MY STATE block, the store and the "
                    "agent-G must all stay ON.  Set self_T.")
            if cfg.inject_regime != "inject":
                raise ChainError(
                    f"seed_absent=True with inject_regime="
                    f"{cfg.inject_regime!r} is incoherent: the "
                    "reconstruct regime already asks the agent to "
                    "rebuild from memory (there is no injected seed to "
                    "withhold).  S- is the inject regime's code path "
                    "with the derivation suppressed; set "
                    "inject_regime='inject'.")
        if cfg.inject_regime == "inject" and cfg.reconstructor is not None:
            raise ChainError(
                "inject_regime='inject' with a reconstructor injected: "
                "the control arm must not run a reconstruction call, or "
                "the two arms differ in more than the declared variable "
                "(C2).  Remove the reconstructor or run 'reconstruct'.")
        # THE VOCATION SEAT'S PRECONDITIONS (item 13), REFUSED through the
        # LAYER'S OWN guard rather than a second copy of the rule here
        # (one implementation, exercised by V12): the what-for line lands
        # in a block the SELF seat renders, and the criteria are store
        # content reached by the PRICED reconstruction — so vocation=True
        # with either seat absent is refused with BOTH ways out named.
        if cfg.vocation:
            from vocation import check_seat_prereqs
            check_seat_prereqs(vocation=True, self_T=cfg.self_T,
                               retrieval_attached=bool(_seat))
        if cfg.retrieval_priced or cfg.retrieval_decay != 1.0:
            from retrieval import (AccessEpochs, AffordabilitySelector,
                                   RetrievalSeat)
            # THE INJECTION SIDE'S DECODER (item 'codec'): when the
            # codec pair is injected, the priced seat decodes
            # envelope-carrying values through the codec layer WITH THE
            # QUERY — the retrieval cue the GIST reconstruction
            # conditions on (schema and identity ignore it by
            # construction, STATED at the codecs).  With no pair (the
            # default) the decoder is None and the seat is exactly the
            # pre-codec construction, byte-identical.
            _dec = None
            if cfg.codec_policy is not None:
                from memory_codec_seat import decode_value as _dv

                def _dec(stored, *, query=""):
                    return _dv(stored, cfg.codec_registry,
                               query=query)
            self.retrieval = RetrievalSeat(
                selector=AffordabilitySelector(),
                epochs=AccessEpochs(decay_rate=cfg.retrieval_decay),
                priced=cfg.retrieval_priced,
                envelope_decoder=_dec)
        # the routing seat (R5): attached ONLY when the config INJECTS an
        # externally-built selector — the harness never constructs one,
        # and no mechanism module writes the criterion namespace (the
        # battery's R3/R9).  Window construction IS a consolidation
        # boundary, so the criterion is loaded here (and again at each
        # later boundary) and never per turn: R2's timescale, enforced by
        # where the load sits, tested by part R2.
        self.routing_selector = cfg.routing_selector
        self.boundary = None
        self.routing_window = None
        self.routing_criterion = None
        if cfg.routing_selector is not None and cfg.routing_via_boundary:
            raise ChainError(
                "routing_selector AND routing_via_boundary are both set: "
                "two selection seats, one process — refusing rather than "
                "silently preferring one (the in-process seat would "
                "reopen the criterion/selector surface R6 exists to "
                "close).  Set routing_selector=None for the boundary arm")
        if cfg.routing_selector is not None or cfg.routing_via_boundary:
            from routing import RoutingLaw, RoutingWindow
            # THE LAW IS TOLD THE SUBSTRATE'S ACTUAL ARMING LEVEL.  R2's
            # criterion is "keep E below the level at which the switch
            # arms"; in THIS substrate that level is the plant's OWN
            # switch level Theta*S/S_rest, because the plant runs the
            # frozen model's floorless switch (see the module docstring).
            # The value is read from the SAME AgentConfig the plant was
            # built with, so the two cannot drift — with floor=None it is
            # 0.0, i.e. the model's own level, and the law's model-only
            # behaviour is exactly reproduced.  A caller-supplied law that
            # names a DIFFERENT non-zero arm level is REFUSED rather than
            # silently overridden (fail-closed, the load_criterion
            # precedent).
            #
            # HISTORY, because the same defect has now been fixed twice
            # from both sides: pre-round-1 the router gated on the bare
            # Theta*S/S_rest while the plant clamps at max(..., 0.7) and
            # throttled a healthy plant (thetafix class, over-conservative);
            # round 1 told it the 0.7 floor; round 2 removed the floor from
            # the plant's switch and the law follows the substrate down to
            # the model's own level.
            base_law = (cfg.routing_law if cfg.routing_law is not None
                        else RoutingLaw())
            sn_floor = self.agent.cfg.sn.floor
            floor = float(sn_floor) if sn_floor is not None else 0.0
            if base_law.arm_floor != 0.0 and base_law.arm_floor != floor:
                raise ChainError(
                    f"the injected routing law gates at arm_floor="
                    f"{base_law.arm_floor!r} but this substrate's switch "
                    f"arms at max(Theta*S/S_rest, {floor!r}) "
                    f"(AgentConfig.sn.floor) — a router gating on a level "
                    f"the protected mechanism does not use is refused, not "
                    f"silently re-pointed (thetafix class).  Drop the "
                    f"arm_floor from the law, or align the substrate's")
            self.routing_window = RoutingWindow(
                law=replace(base_law, arm_floor=floor))
            if cfg.routing_via_boundary:
                # THE BOUNDARY SEAT (item 13a): the client's
                # construction is the ONLY place the harness touches the
                # handle; the criterion comes back over the socket in
                # reload_criterion() below.
                from boundary_client import BoundaryClient
                self.boundary = BoundaryClient(cfg.boundary_socket or None)
            self.reload_criterion()
        tok = WriterToken.issue("stage2")
        # THE SELF'S COMMITMENTS SEAT (the plan's decision 4 grammar).
        # Attached ONLY when the self seat is on (self_T set); None
        # otherwise, so the default path's batch carries `commitments=()`
        # and the CEN registers nothing.  The CEN hosts the channel; the
        # tracker itself lives here, in selfmodel.py (it is RAM state and
        # rides the C8 checkpoint).
        self.commitment_tracker = None
        self.commitment_reports: list = []
        if cfg.self_T is not None:
            from selfmodel import SELF_PREDICATES, CommitmentTracker
            _ = SELF_PREDICATES          # the grammar this seat extends
            self.commitment_tracker = CommitmentTracker(
                horizon=float(cfg.self_T))
        # THE ACTION SEAT'S TWO HALVES (the tool-call layer), attached ONLY
        # when cfg.actions — absent (None), not inert, otherwise, so a
        # default construction does not even import the module (the
        # vocation/retrieval convention).  The split is the design: the
        # TRACKER is the CEN's inward seat (register, never check), the
        # WORLD is the harness's third surface (apply, never touch the
        # plant).  The world's admissible set is the CALLER's (EXTERNALLY
        # OWNED, default empty) and is the ONLY thing that decides what
        # the grammar admits: with it empty, `complete(tNN)` is prose.
        self.action_tracker = None
        self.toolworld = None
        if cfg.actions:
            from actions import ActionTracker, AdmissibleActions, ToolWorld
            adm = cfg.action_admissible
            if not isinstance(adm, AdmissibleActions):
                # None (the default) or a bare iterable of names is
                # NORMALIZED through the same class, so a caller cannot
                # silently get a different gate than the one they named —
                # and the harness still never constructs a WIDER one than
                # it was handed.
                adm = AdmissibleActions(adm or ())
            self.action_tracker = ActionTracker()
            self.toolworld = ToolWorld(admissible=adm,
                                       effect=cfg.tool_effect,
                                       source=cfg.action_source,
                                       echo_window=cfg.world_echo_window)
            # THE REAL-TOOL SURFACE (worker prerequisite 3): the
            # designer-constructed harness materialises its DECLARED
            # TARGETS into its own sandbox copy (one fresh tree per
            # target, the held-out tree and caches excluded) and its
            # manifest is handed to an emitter that carries the seat (an
            # LLM_DMN reads `tools_manifest`; anything else — fixtures —
            # renders it themselves, which the battery's RT2 does).  NO
            # construction here: the harness object is the caller's,
            # externally owned, default absent.
            if cfg.tools is not None:
                cfg.tools._materialise()
                man = cfg.tools.manifest()
                if getattr(cfg.dmn, "tools_manifest", None) is None \
                        and hasattr(cfg.dmn, "__dict__"):
                    cfg.dmn.tools_manifest = man
        self.cen = CEN(engine=_seed_engine(cfg),
                       record=DurableRecord(record_path, tok),
                       budget=cfg.budget, levers=cfg.levers, token=tok,
                       retrieval=self.retrieval,
                       commitments=self.commitment_tracker,
                       actions=self.action_tracker,
                       encoding_gate=self.encoding_gate)
        self.dmn = cfg.dmn if cfg.dmn is not None else _StubDMN().batch
        self.turn = 0
        # the CEN's REAL backlog STOCK, EMA'd at tau_D — TELEMETRY.  A
        # stock count is neither the model's B nor on the model's scale,
        # and it drives nothing (see the module docstring).  Kept so the
        # raw backlog's own trajectory stays visible.
        self.backlog_ema = 0.0
        # TELEMETRY — NOT the P2 addend.  The per-turn UNCHECKABLE share of
        # what the generator offered (u/n, dimensionless, [0,1]), EMA'd at
        # 1/tau_D: the CEN's real reading of the unchecked-accrual rate.
        # The P2 addend the plant's D carries is the plant's OWN B
        # (Agent.B = the EMA at tau_D of the plant's switch state c, logged
        # per turn as Stage2LogRow.edge_addend); u/n is kept because it is
        # the substrate's measurement and must stay visible beside the
        # quantity the model's one c actually is.
        self.backlog_rate = 0.0
        # THE P2 ADDEND B THE PLANT'S D IS ACTUALLY DRIVEN WITH (same
        # statement as Stage2LogRow.edge_addend, held as state so a
        # resumed run's first consolidation boundary gates on the plant's
        # real number rather than on 0.0).  Set from the plant's own log
        # in _plant_step; 0.0 before the first turn and whenever the
        # coupling is off.
        self.p2_addend = 0.0
        self.log: list[Stage2LogRow] = []
        # cross-boundary plant snapshot the DMN reads (never the reverse:
        # the DMN sees plant telemetry, the plant never sees the DMN's
        # internals except through the currency)
        self.last_plant: dict = {}
        # the RECONSTRUCTED SELF the next DMN turn reads — the
        # reconstruction's ONLY consumer (retrieval.py's
        # Reconstruction.text; §11c: it had none).  Set after check_turn
        # from the turn's RetrievalOutcome; "" when the retrieval seat is
        # off (the pre-retrieval baseline, byte-identical) or when the
        # affordable prefix covered nothing.  Carried by _CP_SCHEMA, so a
        # resume cannot silently lose the context the next turn reads.
        #
        # PER-TURN, AND THAT IS THE CHARGE'S TIMESCALE (§11c): the
        # retrieval runs EVERY turn and is PRICED every turn (charged
        # first inside check_turn), because the self is not carried on
        # the working set (survivability.md:68).  It is NOT what the DMN
        # is handed when the self seat is on — see `self_block` below.
        self.dmn_self: str = ""
        # -- THE SELF'S PER-WINDOW STATE (§11d's self subsection) --------
        # THE INJECTED BLOCK IS PER-WINDOW; THE CHARGE IS PER-TURN.  The
        # reconciliation is stated here once, because §11c's per-turn
        # charge and the self's per-window injection are the two readers
        # that must not contradict each other: the retrieval is priced
        # EVERY turn (the standing inward cost, §11c — that is what makes
        # the self depletable at all), and the BLOCK the generator is
        # handed is captured ONCE at a consolidation boundary (tau_S =
        # TAU_S_TURNS turns) and HELD for the window's turns.  Window 1
        # gets the BASE SELF (the derivation seed — the pristine INITIAL
        # CONDITION, decision 1: it is never re-injected, and every later
        # window gets the RECONSTRUCTED self, a lossy reconstruction of
        # the agent's own persisted self_content).
        self.self_windows: int = 0        # boundaries observed
        # -- THE MEMORY'S PER-WINDOW SCHEDULE (item 'retrieval' / C20) ----
        # THE THIRD, INDEPENDENT WINDOW.  `self_windows` schedules the
        # SELF's block and `routing_window.windows` the routing law's f;
        # this one schedules C20's CONSOLIDATION — the act that makes the
        # retrieval weight decay (`AccessEpochs.consolidate`, the ONLY
        # thing that advances `_consolidations`, and therefore the only
        # thing that makes `Stage2Config.retrieval_decay` bind at all).
        # It is INDEPENDENT of both: the retrieval seat can exist with
        # `self_T=None` and no routing selector at all (they are separate
        # config switches, and this seat's own guard — decay != 1.0
        # requires priced — names neither), so this boundary must not be
        # nested inside the routing block nor inside self_window_boundary
        # (which RETURNS EARLY when self_T is None).  `memory_windows`
        # counts the boundaries OBSERVED, exactly as `self_windows` does,
        # and is carried by _CP_SCHEMA so a resume neither double-counts
        # nor loses one.  It stays 0 on the default path (no seat -> the
        # due-predicate is False), which is what keeps the default loop
        # byte-identical: with no seat there is nothing to consolidate.
        self.memory_windows: int = 0      # C20 boundaries observed
        # -- THE MEMORY-CODEC SEAT (item 'codec'; DEFAULT OFF) -----------
        # The INJECTED policy+registry pair, validated at construction
        # and held here; `memory_window_boundary` calls the seat ONLY
        # when both are present.  None (the default) = the codec layer
        # does not exist on the run path and the boundary is exactly
        # C20's consolidate() — byte-identical to the pre-codec loop.
        # `codec_report` is the LAST boundary's pass (a log/audit
        # surface; NOTHING on the run path reads it back, so it is not
        # checkpoint state — the S10 exclusion; the envelopes live in
        # the STORE and the decisions in the RECORD).
        self.codec_report = None
        self._codec_seat_validate(cfg)
        # -- THE DRIVE'S OWN WINDOW (A3, the F5 decoupling) ----------------
        # `self_windows` schedules the self's BLOCK, and before this the
        # drive rode that boundary — so a drive-wired arm with the self seat
        # OFF never wrote a drive at all (the boundary it lived in returned
        # early).  This counter schedules THE DRIVE ALONE, on the same
        # tau_S = TAU_S_TURNS timescale, for the arm whose emitter has an
        # inward channel but is handed no self-description.  It stays 0
        # unless `cfg.drive_seat` is set AND the self seat is off, so the
        # default path and every self-seat arm are unchanged — and when
        # BOTH are on the self's own boundary owns the drive and this
        # counter never advances, which is what makes "exactly one
        # set_drive per window" structural rather than a convention.
        self.drive_windows: int = 0       # drive-only boundaries observed
        self.self_block: str = ""         # the window's injected SELF
        # THE ARM'S OWN OUTPUT at the last (re)generation — the seed in the
        # inject arm, the AGENT'S answer in the reconstruct arm.  Logged so
        # the fidelity of what the agent actually said can be scored from
        # the record rather than re-derived.
        self.last_reconstruction: str = ""
        self.last_reconstruction_turn: int | None = None
        self.self_model_block: str = ""   # the window's model-of-itself
        self.self_inward_sum: float = 0.0  # the window's inward-share acc
        self.self_inward_n: int = 0
        self.self_drive: float = 0.0      # the a_hold drive in force
        self.coverage: float = 1.0        # last turn's Reconstruction.coverage
        self.recon_candidates: int = 0    # last turn's candidate count
        #: THE LAST TURN'S RETRIEVAL CHARGE in C11 derivations, as the
        #: seat's own outcome reported it (`RetrievalOutcome.derivations`,
        #: READ — one source; see the loop's assignment for why this is a
        #: measurement seat, never a plant input).  0 with no seat
        #: attached.
        self.retrieval_derivations: int = 0
        self.open_commitments: int = 0
        self.commitments_expired: int = 0
        # -- SELECTIVE ENCODING OBSERVABLES (item 'encoding'; the gate
        # itself is CEN-side — these are the harness's read of the
        # per-turn GateOutcome, for the log and the checkpoint, carried
        # by _CP_SCHEMA like `coverage`/`recon_candidates` are: the
        # campaign's audit surface, so a resumed run's counters do not
        # restart from zero).  0.0/0/0 with no gate attached.
        self.encode_salience: float = 0.0   # last turn's combined salience
        self.encode_admitted: int = 0       # 1 iff it entered the
                                            # consolidating tier
        self.encode_denied: int = 0         # cumulative denials to the
                                            # lower tier (the gate's own
                                            # audit counter — the
                                            # suppression must stay
                                            # countable, never a silent
                                            # drop)
        # THE SEED, INSTALLED ONCE (decision 1 — the initial condition,
        # never a fixture).  It goes in THROUGH THE CEN'S OWN WRITE PATH
        # (`engine.txn_commit` with the CEN's token, the same fact shape
        # check_turn writes for `self_content`), so the seed is ordinary
        # priced store content from its first moment: subject to the same
        # coverage loss, never pinned, never re-injected.
        if cfg.seed_self:
            from selfmodel import seed_store
            self.seed_rev = seed_store(self.cen.engine, self.cen.token)
        else:
            self.seed_rev = None
        # -- THE VOCATION (item 13): the gate runs HERE, once, at
        # construction, and its outcome is the layer's state ------------
        # THE CRITERIA GO IN THROUGH THE ENGINE'S OWN WRITE PATH with the
        # CEN's token (`install_vocation`, `seed_store`'s fact shape and
        # discipline one relation over), so they are ordinary priced store
        # content from their first moment — subject to the same coverage
        # loss, never pinned.  THE ONE DECISION THAT KEEPS THE DEFAULT
        # LOOP UNTOUCHED even with the layer ON: the criteria's relation
        # (`vocation`) is enumerated by NOTHING per turn — the retrieval
        # seat stays over `self_content` ONLY — so this install cannot
        # change what any turn reads; V9 measures that bit-identity, with
        # its two falsify arms.
        #
        # THE STATE IS ABSENT — `None`, not an inert object — WHEN THE
        # SWITCH IS OFF (the cen.retrieval / routing_window /
        # cen.commitments convention), so a default construction does not
        # even IMPORT the module: the default loop is untouched at the
        # level of its imports, not merely in its bytes (V4 measures
        # both; the checkpoint carries a stable None).
        #
        # A RESUME RE-RUNS THIS CONSTRUCTOR (the seed's own precedent:
        # `seed_self` re-installs at the same keys).  The engine is then
        # REPLACED by the checkpoint's own dump when the schema walk
        # reaches `cen.engine`, and the layer's state by the checkpoint's
        # own (`_vocation_cp_set`) — so a resumed run holds the vocation
        # the checkpoint holds, and a resume config that DISAGREES with it
        # REFUSES there rather than silently re-picking.
        self.vocation = None
        if cfg.vocation:
            from vocation import VocationState, gate, install_vocation
            self.vocation = VocationState(enabled=True)
            _out = gate()
            self.vocation.note(_out.record, _out.line())
            install_vocation(self.cen.engine, self.cen.token, _out.record)

    # -- the P2 coupling surface --------------------------------------------
    def _advance_backlog_ema(self, backlog: int) -> float:
        """One step at rate 1/tau_D with the exact ZOH recursor — never
        Euler (same discipline as every other lag in this codebase).
        TELEMETRY: this is the CEN's real backlog STOCK (assertions
        outstanding), EMA'd.  It is not the model's B (a stock count has
        no counterpart in the model) and it drives nothing — the P2
        addend is the plant's own B = EMA_tauD(c) (Stage2LogRow.
        edge_addend)."""
        lam = 1.0 / self.p.tau_D
        self.backlog_ema = zoh_lag(self.backlog_ema, float(backlog), lam,
                                   H_STEP)
        return self.backlog_ema

    # -- the self's per-window surface (§11d's self subsection) --------------
    def self_window_due(self, turn: int) -> bool:
        """Is `turn` a CONSOLIDATION BOUNDARY for the self?  True at the
        first turn of a fresh state and every TAU_S_TURNS turns — the
        same timescale the routing criterion reloads on (tau_S = 100),
        and deliberately INDEPENDENT of the routing seat (the self must
        work with routing off).  False whenever the self seat is off
        (`self_T` None), which is what keeps the default loop unchanged."""
        if self.cfg.self_T is None:
            return False
        return self.self_windows == 0 or turn % TAU_S_TURNS == 0

    def _regenerate_self_block(self) -> str:
        """THE ARM'S RULE, APPLIED ONCE PER COMPACTION.

        Called when a compaction has landed since the block was last
        generated.  It is the WHOLE arm variable and it is deliberately
        the only place the arms differ:

          "inject"      -> the harness hands the FULL derivation back
                           (render_base_self).  Nothing was lost; the
                           agent never pays.  THE CONTROL.
          "reconstruct" -> the AGENT answers, from what the compaction
                           left (reconstruct_self).  A summary that ate
                           the derivation's grounds yields a thin answer.
                           THE EXPERIMENT.
        """
        if self.cfg.inject_regime == "inject":
            from selfmodel import render_base_self
            # S- (seed_absent): the inject regime's restoration is the
            # seed's THIRD supply channel and the seat WITHHOLDS it --
            # "" again, so the derivation never reappears in any window.
            return ("" if self.cfg.seed_absent
                    else render_base_self())
        return self.reconstruct_self()

    def _conversation_text(self) -> str:
        """What the NAIVE MEMORY holds right now (summary + kept turns) —
        the surface the reconstruction arm is asked to reconstruct from,
        and the same surface the C3 probe reads in the runner.  The path
        (`cfg.dmn` -> its inner emitter -> `memory`) is the one the
        runner's own hook uses; an absent memory yields "" rather than an
        exception, and the caller records that as an empty reconstruction
        rather than inventing content."""
        inner = getattr(self.cfg.dmn, "inner", None) or self.cfg.dmn
        mem = getattr(inner, "memory", None)
        if mem is None:
            return ""
        try:
            return str(mem.conversation_text())
        except Exception:                              # noqa: BLE001
            return ""

    def reconstruct_self(self) -> str:
        """THE AGENT'S OWN RECONSTRUCTION OF ITS SELF, after a compaction
        ate the window the derivation lived in (arm "reconstruct").

        WHAT IT IS: the injected reconstructor, called on the text the
        NAIVE MEMORY holds now (the summary plus the kept turns) — i.e.
        on exactly what the compaction left.  Its answer becomes the
        next window's self block.  It is a GENERATION, not a lookup: the
        agent is being asked what it still knows about itself, and when
        the summary dropped the derivation's grounds the answer is thin.

        WHY THE ENGINEERED STORE IS NOT CONSULTED: `self.dmn_self` is
        the priced retrieval's reconstruction of the persisted
        `self_content` facts, which reproduces the derivation BY
        CONSTRUCTION — using it here would make the self unlosable (the
        whole derivation reappears every window) and the loss identically
        zero, which is exactly the defect that voided campaign 3
        (MEASURED: 65/65 loss readings 0.0; 740/740 rows read
        self_steps == [1,2,3,4]).  The store is still ON and still
        charged (C11/C20); it is simply not the self.

        FAIL-CLOSED: an empty reconstruction is RECORDED as empty, never
        silently replaced by the seed — a harness that put the seed back
        here would erase the phenomenon it is measuring.
        """
        text = self._conversation_text()
        try:
            return str(self.cfg.reconstructor(text) or "")
        except Exception as exc:                      # noqa: BLE001
            raise ChainError(
                f"the injected reconstructor raised on the compacted "
                f"conversation: {exc!r}.  The arm is defined by that call "
                f"happening; a silent fallback to the seed would make the "
                f"loss identically zero (the campaign-3 defect).") from exc

    def self_window_boundary(self, turn: int, sch=None) -> None:
        """ONE consolidation window of the self, at the boundary.

        (i) THE INJECTED BLOCK: window 1 gets the BASE SELF (the
        derivation seed — the pristine initial condition, NEVER
        re-injected), every later window gets `self.dmn_self`, the last
        turn's PRICED reconstruction of the agent's own persisted
        self_content.  IT IS COVERAGE-AFFECTED BY CONSTRUCTION: the
        reconstruction is the priced prefix of what the store offered, so
        a depleted retrieval hands the generator a THINNER self (B1's
        first hop).  (ii) THE SELF-MODEL BLOCK, rendered from CEN-side
        observables only.  (iii) THE a_hold DRIVE: the window that just
        ended is summarised by its mean INWARD SHARE — the part of what
        the agent emitted that stayed inward (R1's unchecked return
        path), measured per turn by `_inward_of` on the emitter's own
        instrument (the model's TRACE against its content when it exposes
        one, the prose/stream share otherwise) — and that number is
        written onto the caller's schedule seat
        (`SelfReferentialDrive.set_drive`) for the window about to run.
        With a plain `Schedule` (no `set_drive`) nothing is written: the
        seat is the caller's and the default is OFF."""
        cfg = self.cfg
        if cfg.self_T is None:
            return
        from selfmodel import render_base_self, render_self_model
        # THIS BOUNDARY NO LONGER OWNS `self_block` (2026-09-29).  The
        # block is (re)generated at the COMPACTION, by the per-turn site
        # in the turn loop, because the arm variable is "who restores the
        # self after a COMPACTION" and compactions are ~10x more frequent
        # than this window (self_T = 100 turns).  While this boundary
        # owned it, the arm did nothing in a 40-turn run (MEASURED: no
        # boundary fired, both arms carried the identical seed).
        # What this boundary still owns is the SELF-MODEL block, the
        # per-window a_hold drive, and the vocation seat below — all of
        # which are correctly per-window.
        if self.self_windows == 0:
            # window 1 seeds the derivation ONCE, identically in both
            # arms; the per-turn site hands it out on the first turn and
            # then regenerates only when a compaction has landed.
            # 0, NOT -1: at window 1 no compaction has landed, so the
            # per-turn site must NOT regenerate yet — the SEED is the
            # initial condition and it is what gets spent on turn 1.
            # MEASURED (the -1 that was here): `0 > -1` fired immediately,
            # the reconstruct arm asked the agent to rebuild its self from
            # an EMPTY conversation, the seed was never injected, and
            # self_steps was [] from turn 1.
            self._comps_seen = 0
            # S- (seed_absent): the window-1 block is the seed's FIRST
            # supply channel and the seat WITHHOLDS it -- an empty block,
            # never a substitute text (a placeholder paragraph would be
            # experimenter-supplied content wearing the seat's name).
            self.self_block = ("" if cfg.seed_absent
                               else render_base_self())
        self.self_drive = (self.self_inward_sum / self.self_inward_n
                           if self.self_inward_n else 0.0)
        if sch is not None and hasattr(sch, "set_drive"):
            sch.set_drive(self.self_drive, turn)
        self.self_inward_sum = 0.0
        self.self_inward_n = 0
        tr = self.commitment_tracker
        # THE VOCATION'S WINDOW SEAT (item 13): the self-model block's
        # what-for line carries the ADOPTED expectation, rendered for this
        # window (the same timescale as the block, tau_S = 100 — the layer
        # is read at the boundary and held).  The substitution is ONE line
        # and it goes through `render_self_model`'s own `what_for`
        # parameter: with no adopted record `render_what_for` returns
        # TODAY'S EXACT text, which IS the parameter's default — so the
        # ON-but-UNADOPTED arm is byte-identical to the pre-vocation
        # block, and the OFF arm does not even import the module.
        _sm_kw: dict = {}
        if self.vocation is not None:
            from vocation import render_what_for
            _sm_kw["what_for"] = render_what_for(self.vocation.record)
        self.self_model_block = render_self_model(
            horizon=float(cfg.self_T), coverage=self.coverage,
            candidates=self.recon_candidates,
            open_commitments=(0 if tr is None else len(tr.open)),
            expired=(0 if tr is None else tr.expired),
            backlog=self.cen.backlog_outstanding(),
            backlog_share=self.backlog_rate,
            budget_total=cfg.budget.derivations_per_turn,
            spent_last=self.cen.ledger.spent_this_turn, **_sm_kw)
        self.self_windows += 1

    # -- the drive's own per-window surface (A3 — the F5 decoupling) --------
    def drive_window_due(self, turn: int) -> bool:
        """Is `turn` a CONSOLIDATION BOUNDARY for the DRIVE ALONE?  True at
        the first turn of a fresh state and every TAU_S_TURNS turns.

        THE F5 DECOUPLING.  The drive is the agent's INWARD CHANNEL reaching
        the plant (`SelfReferentialDrive` -> a_hold); the self seat is
        whether the agent is TOLD its own CEN-measured state.  The model ties
        neither to the other, so gating one on the other was an engineering
        artefact — and a load-bearing one: with `self_T` None the old
        boundary returned early, so a wiring arm that was supposed to move
        the plant could not, and its "no collapse" reading would have been
        the ABSENCE OF A DRIVE rather than the absence of an effect.

        False in BOTH of the cases where this seat must not write:
          * `cfg.drive_seat` unset (the default path, byte-identical), and
          * the self seat ON — `self_window_boundary` already owns the drive
            there, and a second writer in the same window would be two
            `set_drive` calls for one window (and two resets of the
            accumulator it is computed from)."""
        if not self.cfg.drive_seat or self.cfg.self_T is not None:
            return False
        return self.drive_windows == 0 or turn % TAU_S_TURNS == 0

    def drive_window_boundary(self, turn: int, sch=None) -> None:
        """ONE consolidation window of the DRIVE ALONE, at the boundary:
        write the window that just ended's mean INWARD SHARE onto the
        caller's schedule seat, and reset the accumulator.

        THE SAME MEASUREMENT AND THE SAME WRITE as `self_window_boundary`'s
        drive arm — deliberately, and that is the point: the arm without the
        self DESCRIPTION must differ from the arm with it in exactly ONE
        thing (the prompt bytes and the injected block), never in the
        instrument that reaches the plant.  The share is the window's mean
        of `_inward_of` (the emitter's own trace when it declares one, the
        labelled prose fallback otherwise) accumulated per turn by the loop.

        It touches NOTHING else: no self block, no model-of-itself, no
        commitment scoring, no `self_windows` increment — those are the self
        seat's, and this boundary exists precisely because that seat is
        off."""
        if self.cfg.self_T is not None:
            return          # the self's own boundary owns the drive
        self.self_drive = (self.self_inward_sum / self.self_inward_n
                           if self.self_inward_n else 0.0)
        if sch is not None and hasattr(sch, "set_drive"):
            sch.set_drive(self.self_drive, turn)
        self.self_inward_sum = 0.0
        self.self_inward_n = 0
        self.drive_windows += 1

    # -- the memory's per-window surface (item 'retrieval' / C20) -----------
    def memory_window_due(self, turn: int) -> bool:
        """Is `turn` a CONSOLIDATION BOUNDARY for C20's memory?  True at
        the first turn of a fresh state and every TAU_S_TURNS turns — the
        SAME timescale as the self's block and the routing criterion's
        reload (tau_S = 100), and deliberately INDEPENDENT of both those
        seats: the retrieval seat can be attached with `self_T=None` and
        no routing selector (its construction condition is
        `retrieval_priced or retrieval_decay != 1.0`), so a boundary
        nested inside either would leave C20 unscheduled in that arm.
        False whenever the retrieval seat is off, which is what keeps the
        default loop unchanged: with no seat there is no decay to apply."""
        if self.retrieval is None:
            return False
        return self.memory_windows == 0 or turn % TAU_S_TURNS == 0

    def memory_window_boundary(self, turn: int) -> None:
        """ONE consolidation window of the MEMORY, at the boundary: C20's
        `consolidate()` — the decided placement ("decay applied AT
        CONSOLIDATION"), and the ONLY caller of it on the run path.

        WHAT IT DOES AND DOES NOT DO (stated, so the inertness cannot be
        re-argued away): it advances the epoch counter by ONE, which is
        the whole mechanism — `AccessEpochs.weight(key)` is
        `decay_rate ** (consolidations - last_epoch)` evaluated LAZILY, so
        one increment multiplies every entry not accessed since the last
        window by `decay_rate` once.  Nothing is rewritten (in RAM or on
        disk), no entry is dropped, and at `decay_rate = 1.0` the
        weights are arithmetically unchanged (`1.0 ** n == 1.0`) — the
        documented default is still NO decay (err slow); this boundary
        SCHEDULES the decay the seat was built for and does not choose
        its rate.

        THE CODEC SEAT (item 'codec'; DEFAULT OFF): when the config
        INJECTS the policy+registry pair, this boundary is ALSO the
        ENCODE boundary (spec §5: codec choice is ENCODE-TIME, and the
        consolidation boundary is the only legal encode time — B7.1's
        temporal separation).  The call sits AFTER `consolidate()` and
        BEFORE `memory_windows += 1`, and it is the ONLY run-path
        caller of the codec layer.  With the pair ABSENT (the default)
        the call does not exist and this method is byte-identical to
        the pre-codec boundary — the seat convention, asserted by the
        boundary battery's byte-identity part.  The seat APPENDS
        supersession entries (C19: nothing is rewritten — the original
        bytes stay, a refusal keeps them, the gist input is always the
        ORIGINAL) and appends its decisions to the DURABLE RECORD
        before the engine commit (C9).

        The counter advances in the same step as the epoch, so the two
        agree by construction (a boundary that failed to consolidate
        would be a schedule that lies); the log column `memory_epoch`
        reads the SEAT's own number, not this counter, so a dropped
        consolidate() call would show up there as a stalled index beside
        a rising `memory_windows`."""
        if self.retrieval is None:
            return
        self.retrieval.epochs.consolidate()
        # THE WINDOW INDEX the seat's decisions are recorded under:
        # memory_windows+1 is the window that is OPENING (window 1 is
        # the first boundary of a fresh state).  The supersession keys
        # embed it, so every envelope names the boundary that made it.
        _win = self.memory_windows + 1
        if self.cfg.codec_policy is not None:
            from memory_codec_seat import consolidate_codecs
            self.codec_report = consolidate_codecs(
                engine=self.cen.engine, record=self.cen.record,
                token=self.cen.token,
                epochs=self.retrieval.epochs,
                window=_win,
                policy=self.cfg.codec_policy,
                registry=self.cfg.codec_registry)
        self.memory_windows += 1

    def _codec_seat_validate(self, cfg) -> None:
        """Fail-closed validation of the INJECTED codec pair (the
        encoding_gate precedent): exactly both or neither, real objects
        (never names — a caller-chosen name is not a capability, the
        R5 lesson), and the registry must resolve every codec the
        policy may choose.  The harness constructs NOTHING here; it
        only refuses a pair that cannot act."""
        _pol, _reg = cfg.codec_policy, cfg.codec_registry
        if _pol is None and _reg is None:
            return
        if _pol is None or _reg is None:
            which = ("codec_registry" if _pol is not None
                     else "codec_policy")
            raise ChainError(
                f"cfg.{which} is None but its pair is set: the codec "
                f"seat is an INJECTED PAIR (a policy with no registry "
                f"cannot encode; a registry with no policy cannot "
                f"choose).  Set BOTH codec_policy and codec_registry, "
                f"or leave both None (the default, byte-identical)")
        for attr in ("gist_min_chars", "enabled_codecs",
                     "consolidated_tier", "policy_id"):
            if not hasattr(_pol, attr):
                raise ChainError(
                    f"cfg.codec_policy is "
                    f"{type(_pol).__name__}, not a memory_codecs."
                    f"CodecPolicy (no .{attr}): inject a designer-built "
                    f"policy — the harness never constructs one, and a "
                    f"duck-typed lookalike is not a capability (R5)")
        if isinstance(_pol, str) or isinstance(_reg, str):
            raise ChainError(
                "cfg.codec_policy/codec_registry must be the injected "
                "objects, never names — a name the harness resolves "
                "would be the caller-chosen-name defect (R5)")
        if not hasattr(_reg, "get") or not hasattr(_reg, "codec_ids"):
            raise ChainError(
                f"cfg.codec_registry is {type(_reg).__name__}, not a "
                f"memory_codecs.CodecRegistry (no .get/.codec_ids): "
                f"inject a designer-built registry")
        missing = set(getattr(_pol, "enabled_codecs", ())) \
            - set(_reg.codec_ids)
        if missing:
            raise ChainError(
                f"the codec policy enables {sorted(missing)} but the "
                f"injected registry carries no decoder for them "
                f"({sorted(_reg.codec_ids)}) — an enabled-but-absent "
                f"codec is the pretend-latent S3 forbids; the encode "
                f"path would refuse at the first boundary")

    def memory_epoch(self) -> int:
        """The consolidation-window index in force, READ OFF THE SEAT
        (`AccessEpochs.consolidations`, the quantity `weight()` actually
        uses) — 0 when the seat is off.  This is the per-turn log's
        `memory_epoch` column; it is deliberately NOT a re-derivation
        from `memory_windows` (the two must AGREE, and the log should
        show it if they ever do not)."""
        return 0 if self.retrieval is None \
            else int(self.retrieval.epochs.consolidations)

    def score_commitments(self, turn: int):
        """THE BOUNDARY SCORING (the plan's Q4).  Every DUE commitment
        (`deadline <= turn`) is scored by a REAL engine lookup, each
        charging its engine-reported cost FIRST through the SAME C11
        ledger the assertions use; a due commitment the boundary turn
        cannot afford is DEFERRED and stays open.  FULFILLED if
        `done(target)` holds, otherwise EXPIRED — an OBSERVABLE, never
        debt (expiry-as-debt would add a new self-to-D coupling edge,
        C26c).  Returns the report, or None when the seat is off.

        PLACEMENT, stated precisely rather than asserted: the scoring
        runs at the END of the boundary turn's CEN work (immediately
        after `check_turn`), because the per-turn ledger is the only
        per-turn cost gate and `check_turn` opens it — so the charge sits
        in the boundary turn's real spend and is bounded by the same
        per-turn budget, never a side ledger."""
        tr = self.commitment_tracker
        if tr is None:
            return None
        rep = tr.score(turn=turn, engine=self.cen.engine,
                       ledger=self.cen.ledger, budget=self.cfg.budget)
        self.commitment_reports.append(rep)
        self._sync_commitment_observables()
        return rep

    def _sync_commitment_observables(self) -> None:
        """The two goal-generation observables the per-turn log carries:
        the OPEN SET SIZE and the cumulative expiry count.  Zero when the
        seat is off (the default), so the log's new fields are inert."""
        tr = self.commitment_tracker
        self.open_commitments = 0 if tr is None else len(tr.open)
        self.commitments_expired = 0 if tr is None else tr.expired

    def _commitments_cp_get(self):
        return None if self.commitment_tracker is None \
            else self.commitment_tracker.dump()

    def _commitments_cp_set(self, v) -> None:
        """C8, fail-closed, the `_routing_crit_set` precedent: a
        checkpoint that carries a tracker may not be resumed into a
        config with no tracker (and vice versa) — either way the open
        commitment set would be silently lost, and an empty open set
        reads as 'no goals', which is a MEASURED-looking artifact of a
        dropped field."""
        cur = self.commitment_tracker
        if v is None and cur is None:
            return
        if cur is None:
            raise ChainError(
                "the checkpoint carries a commitment tracker but the "
                "resume config sets no self seat (self_T=None) — "
                "REFUSING the resume (C8: the open commitment set would "
                "be silently emptied)")
        if v is None:
            raise ChainError(
                "the resume config sets a self seat (self_T is not None) "
                "but the checkpoint carries no commitment tracker — "
                "REFUSING the resume (C8: the read surface must be "
                "restored, not silently dropped)")
        cur.load(v)

    # -- the encoding-gate surface (item 'encoding') ----------------------
    def _encoding_cp_get(self):
        if self.encoding_gate is None:
            return None
        p = self.encoding_gate.policy
        # JSON-safe canonical form (the checkpoint is round-tripped
        # through json by the C8 consumers; a frozenset is not).
        return {"policy_id": p.policy_id, "threshold": p.threshold,
                "mode": p.mode, "low_tier": p.low_tier,
                "seed_weight": p.seed_weight,
                "signals": sorted(p.signals)}

    def _encoding_cp_set(self, v) -> None:
        """C8, fail-closed, the `_commitments_cp_set` precedent: a
        checkpoint that carries an encoding policy may not be resumed
        into a config with a different one (and vice versa) — either
        way the campaign's tier decisions would silently change
        meaning mid-run, and `encode_denied` would count denials under
        two different policies.  The match is on the policy's OWN
        fields, in the getter's canonical form."""
        cur = self.encoding_gate
        if v is None and cur is None:
            return
        if cur is None:
            raise ChainError(
                "the checkpoint carries an encoding policy but the "
                "resume config injects no encoding gate — REFUSING the "
                "resume (C8: the campaign's tier decisions would "
                "silently change meaning)")
        if v is None:
            raise ChainError(
                "the resume config injects an encoding gate but the "
                "checkpoint carries no encoding policy — REFUSING the "
                "resume (C8: a mid-campaign policy change is not a "
                "resume)")
        have = self._encoding_cp_get()
        if v != have:
            raise ChainError(
                f"the resume config's encoding policy differs from the "
                f"checkpoint's ({have} vs {v}) — REFUSING the resume "
                f"(C8: re-tiering mid-campaign is a new campaign, not "
                f"a resume; the policy is the designer's to change "
                f"between campaigns)")

    # -- the vocation surface (item 13) -------------------------------------
    def _vocation_cp_get(self) -> dict | None:
        """The layer's carried state (`VocationState.dump`), or None when
        the layer is off — the conditional-None convention, so the key is
        ALWAYS PRESENT (S10's shape gate) and a default run serializes a
        stable None."""
        return None if self.vocation is None else self.vocation.dump()

    def _vocation_cp_set(self, v) -> None:
        """C8, FAIL-CLOSED (the `_commitments_cp_set` / `_routing_crit_set`
        precedent): a resume must not silently DROP an adopted expectation
        the checkpoint holds, nor ADOPT one mid-run.  Both mismatches are
        refused by the layer's own guard (`vocation.guard_resume_vocation`,
        the `_guard_resume_drive` pattern one layer over), which names both
        ways out.

        ORDER, AND WHY: the guard reads the CHECKPOINT's own `enabled` /
        `gate_ran` flags, so it runs on the LOADED state before that state
        replaces the one this construction produced (which ran the gate
        fresh — a resume re-runs the constructor, so the fresh outcome is
        the wrong answer for every case the checkpoint speaks to).  The
        state is then taken from the checkpoint ONLY when the checkpoint
        says the layer existed: an off-resumed-off run keeps `None`, so
        the "state is None iff the layer is off" invariant survives the
        resume."""
        from vocation import VocationState, guard_resume_vocation
        ck = VocationState()
        if v is not None:
            ck.load(v)          # fail-closed on a mangled record
        guard_resume_vocation(enabled=bool(self.cfg.vocation), state=ck)
        if ck.enabled:
            self.vocation = ck

    # -- the memory-codec seat's C8 surface (item 'codec') ------------------
    def _codec_cp_get(self):
        """The INJECTED codec policy's IDENTITY — policy_id only, the
        designer-visible shape (the `cen.encoding` precedent: the
        checkpoint carries what a resume must MATCH, never the
        mechanism's runtime).  None when the seat is off, so the key is
        ALWAYS PRESENT (S10's shape gate) and a default run serializes
        a stable None."""
        return None if self.cfg.codec_policy is None \
            else {"policy_id": self.cfg.codec_policy.policy_id}

    def _codec_cp_set(self, v) -> None:
        """C8, FAIL-CLOSED (the `_encoding_cp_set` precedent): the
        envelopes the store carries were encoded under ONE policy — a
        resume that swaps the policy mid-campaign would silently change
        what every stored Z means (the codec ids would resolve against
        a different rule set at the next boundary).  Both mismatches
        are refused with both ways out named: a checkpoint taken with
        the codec ON resumes only into a config that injects the SAME
        policy_id, and a codec-less checkpoint resumes only into a
        codec-less config."""
        cur = self._codec_cp_get()
        if v == cur:
            return
        raise ChainError(
            f"the checkpoint's codec seat ({v!r}) and the resume "
            f"config's ({cur!r}) disagree — REFUSING the resume (C8: "
            f"the store's envelopes were encoded under one policy; "
            f"re-encoding under another mid-campaign is a new "
            f"campaign, not a resume).  Resume with the same injected "
            f"codec_policy, or from a codec-less checkpoint with both "
            f"fields None")

    # -- the tool-call seat's C8 surface (the talking channel) -------------
    def _actions_cp_get(self):
        """The tool-call seat's carried state — the CEN's ACTION TRACKER
        and the harness-side TOOLWORLD — or None when the seat is off
        (the conditional-None convention, so the key is ALWAYS PRESENT
        (S10's shape gate) and a default run serializes a stable None).

        ONE KEY CARRIES BOTH HALVES, and that is deliberate: they are one
        seat's two sides (the CEN registers/emits, the world applies), so
        a resume cannot restore one without the other.  The world's dump
        includes the ADMITTED SET (the gate in force), so a resume whose
        config names a different gate is caught by the setter below rather
        than silently swapped mid-run."""
        if self.action_tracker is None:
            return None
        return {"tracker": self.action_tracker.dump(),
                "world": self.toolworld.dump()}

    def _actions_cp_set(self, v) -> None:
        """C8, FAIL-CLOSED (the `_commitments_cp_set` / `_routing_crit_set`
        precedent): a checkpoint that carries the tool-call seat may not be
        resumed into a config WITHOUT it (`actions=False`), and a config
        with the seat may not be resumed from a checkpoint without it —
        either way the world's ledger and the registered intents would be
        silently emptied, and an empty ledger reads as "the agent never
        acted", which is a MEASURED-looking artifact of a dropped field.
        A DIFFERENT ADMISSIBLE SET also REFUSES: the gate is a
        construction parameter re-supplied by the caller, and a resume that
        quietly changed what is callable would be the mid-window criterion
        swap one layer over.  Both ways out are named."""
        from actions import AdmissibleActions
        if v is None and self.action_tracker is None:
            return
        if self.action_tracker is None:
            raise ChainError(
                "the checkpoint carries tool-call state but the resume "
                "config sets actions=False — REFUSING the resume (C8: the "
                "world's ledger and the registered action set would be "
                "silently emptied, and an empty ledger reads as 'the agent "
                "never acted').  Set actions=True to run the arm.")
        if v is None:
            raise ChainError(
                "the resume config sets actions=True but the checkpoint "
                "carries no tool-call state — REFUSING the resume (C8: the "
                "read surface must be restored, not silently dropped). "
                "Resume from a checkpoint taken with actions=True.")
        if not isinstance(v, dict) or "tracker" not in v or "world" not in v:
            raise ChainError(
                f"the checkpoint's tool-call state is not this seat's shape "
                f"({sorted(v) if isinstance(v, dict) else type(v).__name__})"
                f" — REFUSING the resume")
        want = AdmissibleActions.load(v["world"].get("admissible"))
        have = self.toolworld.admissible.predicates
        if want.predicates != have:
            raise ChainError(
                f"resume admissible-action set mismatch: the checkpoint's "
                f"gate admits {sorted(want.predicates)} but the resume "
                f"config's admits {sorted(have)} — what is callable would "
                f"change mid-run.  REFUSING; construct the resume state "
                f"with the checkpoint's own action_admissible.")
        self.action_tracker.load(v["tracker"])
        self.toolworld.load(v["world"])

    # -- the real-tool surface's C8 identity -------------------------------
    def _tools_cp_get(self):
        """The tool seat's callable identity, or None when off (the
        conditional-None convention, so the key is ALWAYS PRESENT)."""
        if self.cfg.tools is None:
            return None
        return self.cfg.tools.dump()

    def _tools_cp_set(self, v) -> None:
        """C8, FAIL-CLOSED: a checkpoint carrying a tool seat may not be
        resumed without one (the answers would have no carrier), a
        tool-seat config may not resume a tool-less checkpoint, and a
        harness whose DECLARED TARGETS or ALLOWED TOOLS differ REFUSES —
        what is callable must not change mid-run (the admissible-set
        discipline, one seat over)."""
        if v is None and self.cfg.tools is None:
            return
        if self.cfg.tools is None:
            raise ChainError(
                "the checkpoint carries a tool seat (real-tool surface) "
                "but the resume config supplies none — REFUSING the "
                "resume (C8: the tool answers would have no carrier and "
                "the manifest would silently vanish from the prompt).  "
                "Supply cfg.tools, or resume from a tool-less checkpoint.")
        if v is None:
            raise ChainError(
                "the resume config supplies a tool seat but the "
                "checkpoint carries none — REFUSING the resume (C8: the "
                "resume would enable a surface the run never ran with).  "
                "Resume from a checkpoint taken with cfg.tools set.")
        try:
            self.cfg.tools.load(v)
        except (ValueError, AttributeError) as e:
            raise ChainError(
                f"resume tool-seat mismatch ({e}) — REFUSING: what is "
                f"callable must not change across a resume") from e

    # -- the routing surface (R5) -------------------------------------------
    def reload_criterion(self) -> None:
        """THE CONSOLIDATION BOUNDARY'S CRITERION RELOAD (R2's timescale:
        tau_S = TAU_S_TURNS turns, plus the first turn of a fresh state).
        Called at window construction and at every later boundary, NEVER
        per turn — so a mid-window designer publish is invisible until
        the next window whichever seat is in force.

        TWO SEATS, ONE TIMESCALE.  The LOCAL seat reads the criterion
        file in THIS process (the pre-boundary behaviour, unchanged).
        The BOUNDARY seat (cfg.routing_via_boundary) asks the daemon over
        the socket: the daemon holds the criterion and its anchor in ITS
        OWN privilege domain, so this process never opens the criterion
        file at all — the battery's B6 asserts that with a construction
        spy, which is what makes a silent fallback to the local read FAIL
        there instead of passing unnoticed."""
        if self.boundary is not None:
            self.routing_criterion = self.boundary.crit()
            return
        from routingcrit import RoutingCriterionStore, load_criterion
        self.routing_criterion = load_criterion(
            RoutingCriterionStore(self.cfg.routing_criterion_dir or None))

    def _routed_f(self) -> float | None:
        """This turn's APPLIED fraction: the current window's law output,
        CLIPPED by the externally-owned criterion's [f_min, f_max].  The
        criterion therefore BINDS the realization (the clip and the rule);
        the law supplies the number (routing.py, model-derived).  NO FILE
        READ: the criterion object is the one loaded at the last
        consolidation boundary, so a mid-window designer publish is
        invisible until the next window (R2's timescale, part R2's
        falsifier).  Returns None when no routing seat is attached.

        WITH THE BOUNDARY SEAT THIS IS NOT USED: the daemon applies the
        clip against the criterion IT holds (same rule, same criterion,
        daemon-side authority), so the harness hands over the LAW's raw
        number instead — a caller-applied clip would be a client-side
        decision the boundary exists to remove."""
        w = self.routing_window
        if w is None:
            return None
        c = self.routing_criterion
        if c is None:
            return w.f
        return min(c.f_max, max(c.f_min, w.f))

    def plan_routing(self, turn: int, stream: str,
                     boundary: bool = False) -> tuple:
        """The per-emission application (R5): map this turn's VALID spans
        to CONTENT-BLIND SpanStates and route them through the INJECTED
        selector at the applied fraction.  Returns (selected positions,
        extraction).  A method — never serialized state: the selector is
        a construction parameter (cfg.routing_selector, re-supplied on
        resume exactly as cfg.dmn is), while the window's f IS state and
        is carried by the checkpoint schema.

        `boundary` (item 13a): THIS TURN IS A CONSOLIDATION BOUNDARY, so
        the boundary seat must reload the criterion in the daemon (R2's
        timescale has to hold on BOTH sides of the socket or a mid-window
        publish would move the clip).  The local seat ignores it — its
        criterion object was already replaced by the caller's
        reload_criterion() at the same instant.

        THE PREDICATE SET IS ONE DECLARATION.  The self seat extends the
        grammar (`selfmodel.SELF_PREDICATES` adds `expect`), and the
        selector's POSITION INDICES index the extraction `build_batch`
        will make — so the two extractions must be over the SAME declared
        set, or the routed positions name different spans (MEASURED: the
        default extraction sees `[done(t1)] [done(t3)]` at positions 0,1
        where the extended one sees `done, expect, done` at 0,1,2)."""
        from interleave import extract_spans
        preds = None
        if self.cfg.self_T is not None:
            from selfmodel import SELF_PREDICATES
            preds = SELF_PREDICATES
        if self.boundary is not None:
            return self._plan_routing_boundary(turn, stream, preds, boundary)
        from routingcrit import SpanState
        ex = extract_spans(stream, preds)
        states = tuple(SpanState(predicate=s.predicate, arity=len(s.args),
                                 position=i, turn=turn)
                       for i, s in enumerate(ex.claims))
        return self.routing_selector.plan(states, self._routed_f()), ex

    def _plan_routing_boundary(self, turn: int, stream: str, preds,
                               boundary: bool) -> tuple:
        """THE BOUNDARY ARM of plan_routing (item 13a).  The RAW STREAM
        crosses; the positions come back.  Everything that DECIDES stays
        in the daemon: the extraction, the `SpanState` mapping, the
        selection rule and the [f_min, f_max] clip.  This process holds
        no selector, so the review B2/N6c monkeypatch (replace
        PrefixRoutingSelector, steer turn parity past R3/R4) has no
        object to replace here.

        THE TWO CROSS-CHECKS BELOW ARE THE HARNESS'S OWN, and they are
        LOCAL facts, not a re-derivation of the daemon's decision:
        (i) the daemon echoes the predicate SET it extracted with, and
        it must equal the set this process's own extraction uses, or the
        returned positions would index different spans after a
        cross-tree grammar drift; (ii) every position must be a valid
        index of THIS process's extraction (build_batch/apply_routing
        would refuse an out-of-range one, but the refusal must name the
        boundary, not look like a malformed stream).  Both close a
        LYING DAEMON in the one dimension the harness can check without
        deciding anything — a tampered SHIM is NOT closed by them
        (residual R-c)."""
        from interleave import DECLARED_PREDICATES, extract_spans
        assert self.routing_window is not None
        pos, set_used = self.boundary.route(
            turn, stream, self.routing_window.f,
            self_seat=preds is not None, boundary=boundary)
        expected = DECLARED_PREDICATES if preds is None else preds
        if dict(set_used) != dict(expected):
            raise ChainError(
                f"the boundary daemon extracted with predicate set "
                f"{sorted(set_used)} but this process's grammar is "
                f"{sorted(expected)} — the two trees disagree, so the "
                f"returned positions would index different spans; "
                f"REFUSING (fail-closed, the cross-tree drift guard)")
        ex = extract_spans(stream, preds)
        bad = [p for p in pos if p < 0 or p >= len(ex.claims)]
        if bad:
            raise ChainError(
                f"the boundary daemon returned position(s) {bad} outside "
                f"this turn's {len(ex.claims)} valid spans — refusing "
                f"(the boundary's answer must index THIS extraction)")
        return tuple(pos), ex

    # -- the checkpoint's routing helpers (RAW: specs above) ----------------
    def _routing_cp_get(self) -> dict | None:
        w = self.routing_window
        return None if w is None else {"f": w.f, "windows": w.windows}

    def _routing_cp_set(self, v) -> None:
        if self.routing_window is None or v is None:
            return
        self.routing_window.f = float(v["f"])
        self.routing_window.windows = int(v["windows"])

    def _routing_crit_version(self) -> int | None:
        c = self.routing_criterion
        return None if c is None else int(c.version)

    def _routing_crit_set(self, v) -> None:
        """The criterion BODY is never transported (it has its own
        anchored store); what is checked here is that the version in
        force is the one the checkpoint recorded.  A criterion that moved
        between checkpoint and resume — a designer publish inside the
        window — REFUSES the resume rather than silently swapping the
        rule mid-window (fail-closed, C8)."""
        cur = self.routing_criterion
        if v is None and cur is None:
            return
        if cur is None:
            raise ChainError(
                f"checkpoint carries a routing criterion (v{v}) but the "
                f"resume config injects no selector — REFUSING the "
                f"resume (C8: the read surface must be restored, not "
                f"silently dropped)")
        if v is None or int(cur.version) != int(v):
            raise ChainError(
                f"the routing criterion in force moved between "
                f"checkpoint (v{v}) and resume (v{int(cur.version)}) — a "
                f"mid-window criterion change is refused (R2's "
                f"timescale); re-checkpoint, or resume at a consolidation "
                f"boundary")

    def _plant_step(self, sch: Schedule) -> dict:
        # NOTHING IS INJECTED THROUGH THE SCHEDULE.  The model has ONE c
        # (the plant's switch state), and the coupled arm reads it through
        # the harness's OWN edge (edge_on, set at construction from
        # cfg.couple_backlog) — B = EMA_tauD(c), A_eff = A + B.  The
        # round-1 _CoupledSchedule injection (a second arrival term on the
        # 'A' port, feeding D while the pinning channel read the plant's
        # c) is GONE: it split one model variable into two.
        rec = self.agent.step(sch)
        # the plant's OWN measured addend, held as state (the router's
        # D-analogue reads it at the next consolidation boundary)
        self.p2_addend = float(rec.edge_addend)
        self.last_plant = {"t": rec.t, "a": rec.a, "G": rec.G, "D": rec.D,
                           "S": rec.S, "g": rec.g, "E": rec.E, "c": rec.c,
                           "B": rec.B}
        return self.last_plant

    # -- serialization (the C8 checkpoint surface) ---------------------------
    # THE SCHEMA IS THE CHECKPOINT.  There is ONE flat, declarative
    # source of truth — _CP_SCHEMA below, a class-level constant, NOT
    # a method returning fresh lambdas — and every consumer walks it:
    # to_checkpoint (get), from_checkpoint (shape-gate + set), and the
    # read-surface test S10 (enumerate).  A field cannot be serialized
    # but not restored, or restored without being serialized, and a new
    # state attribute that the turn loop reads FAILS S10 unless it is
    # added HERE — one place, no drift.  This is the structural form of
    # the C8 fix: review B1 (last_plant serialized nowhere while
    # run_stage2 reads st.dmn(turn, st.last_plant)) escaped v1's
    # hand-listed twin field lists; the flat schema makes the two
    # directions the same walk.

    #: checkpoint key -> (getspec, setspec).  Each spec is a dotted
    #: attribute path relative to the Stage2State ("self") or the
    #: string "RAW:<python expr>" for a transform; the resolution rules
    #: live in _cp_get/_cp_set.  Getter-only entries (setter None) are
    #: consumed by the C9 record cross-check, not restored.
    _CP_SCHEMA: dict = {
        "turn": ("turn", "turn"),
        "backlog_ema": ("backlog_ema", "backlog_ema"),
        # the CEN's measured unchecked-accrual share (u/n), EMA'd —
        # TELEMETRY: logged every turn and carried so a resumed run's log
        # keeps the substrate's own measurement.  It drives nothing (the
        # P2 addend is the plant's own B, carried as agent.B / p2_addend).
        "backlog_rate": ("backlog_rate", "backlog_rate"),
        # THE P2 ADDEND B THE PLANT'S D WAS ACTUALLY DRIVEN WITH, on the
        # model's own scale (= the plant's own EMA_tauD(c) when the
        # coupling is on, 0.0 when it is off).  THE ROUTER'S D-ANALOGUE
        # IS BUILT FROM THIS — not from `backlog_rate` (the substrate's
        # telemetry) — so a resume must carry it or the first consolidation
        # boundary after the resume would gate on 0.0 (S10's read surface).
        "p2_addend": ("p2_addend", "p2_addend"),
        # cross-boundary plant telemetry the next DMN turn reads
        # (run_stage2 feeds st.dmn(turn, st.last_plant)) — review B1
        "last_plant": ("RAW:self.last_plant",
                       "RAW:self.last_plant = dict(v)"),
        # the reconstructed self the next DMN turn reads (item
        # 'retrieval' + the DMN generator): a plain dotted-path entry (a
        # str, no transform; its default '' is the attribute's initial
        # value).  The generator is handed
        # {**last_plant, 'retrieved_self': self.dmn_self}, and with the
        # retrieval seat off this is '' = the pre-retrieval context,
        # unchanged.
        "dmn_self": ("dmn_self", "dmn_self"),
        # -- the self's per-window state (§11d's self subsection) --------
        # THE INJECTED BLOCK IS PER-WINDOW; THE CHARGE IS PER-TURN (§11c).
        # `self_block` is the block the generator is handed for the
        # CURRENT window (window 1: the base self; every later window:
        # the reconstruction captured at the boundary); `self_model_block`
        # is the model-of-itself for the window; `self_windows` counts
        # boundaries; the inward accumulator (`self_inward_sum`/`n`) and
        # the drive in force are the a_hold seat's per-window inputs and
        # output.  All are state the next turn reads, so all are carried —
        # dropping one would silently restore the base self or lose the
        # window's drive on a resume.
        "self_windows": ("self_windows", "self_windows"),
        # the MEMORY's own boundary counter (C20's consolidation schedule,
        # the third independent window — see the attribute's comment).  It
        # is state the NEXT turn's due-predicate reads, so it must ride the
        # checkpoint: a resume that lost it would either double-count a
        # boundary (consolidating twice in one window, which is decay
        # applied twice — a fidelity error, not a rounding one) or lose
        # one.  The seat's own epoch counter is NOT duplicated here: it is
        # carried by `cen.retrieval` (AccessEpochs.dump) below.
        "memory_windows": ("memory_windows", "memory_windows"),
        # the DRIVE-ONLY boundary counter (A3).  State the next turn's
        # due-predicate reads, so it must ride the checkpoint for exactly
        # the reason `memory_windows` does: a resume that lost it would
        # either re-take the first-window boundary (writing an extra
        # `set_drive` for a window already driven) or skip one.  It stays 0
        # unless `cfg.drive_seat` is set with the self seat OFF, and the
        # drive VALUE itself is already carried by `self_drive` (which the
        # C8 resume guard compares against the caller's seat).
        "drive_windows": ("drive_windows", "drive_windows"),
        "self_block": ("self_block", "self_block"),
        "self_model_block": ("self_model_block", "self_model_block"),
        "self_inward_sum": ("self_inward_sum", "self_inward_sum"),
        "self_inward_n": ("self_inward_n", "self_inward_n"),
        "self_drive": ("self_drive", "self_drive"),
        # the agent-G observable and the goal-generation observables
        # (coverage / candidates from the retrieval seat's Reconstruction;
        # open/expired from the CommitmentTracker) — carried so a resumed
        # run's law input and log do not restart from 1.0 / 0.
        "coverage": ("coverage", "coverage"),
        "recon_candidates": ("recon_candidates", "recon_candidates"),
        "open_commitments": ("open_commitments", "open_commitments"),
        "commitments_expired": ("commitments_expired",
                                "commitments_expired"),
        # the SELECTIVE-ENCODING observables (item 'encoding'): the
        # last turn's salience and admission, plus the campaign's
        # cumulative denial count — the gate's audit surface, carried
        # like coverage/recon_candidates so a resume neither restarts
        # the counters nor silently loses a tier policy mid-campaign.
        # The POLICY itself is carried by "cen.encoding" (its own
        # fail-closed key below, matched on policy_id).
        "encode_salience": ("encode_salience", "encode_salience"),
        "encode_admitted": ("encode_admitted", "encode_admitted"),
        "encode_denied": ("encode_denied", "encode_denied"),
        "agent.t": ("agent.t", "agent.t"),
        "agent.G": ("agent.G", "agent.G"),
        "agent.D": ("agent.D", "agent.D"),
        "agent.B": ("agent.B", "agent.B"),
        "agent.W_self": ("agent.W_self", "agent.W_self"),
        "agent.W_task": ("agent.W_task", "agent.W_task"),
        "agent.M_self": ("agent.M_self", "agent.M_self"),
        "agent.M_task": ("agent.M_task", "agent.M_task"),
        "agent.sn.a": ("agent.sn.a", "agent.sn.a"),
        "agent.sn.S": ("agent.sn.S", "agent.sn.S"),
        "agent.sn.g": ("agent.sn.g", "agent.sn.g"),
        "agent.sn.monitor_cost": (
            "agent.sn.monitor_cost", "agent.sn.monitor_cost"),
        "cen.turn": ("cen._turn", "cen._turn"),
        "cen.queue": (
            "RAW:[_queue_to_cp(b) for b in cen.queue]",
            "RAW:cen.queue = [_batch_from_cp(b) for b in v]"),
        "cen.debt": ("RAW:list(cen.ledger.debt_assertions)",
                     "RAW:cen.ledger.debt_assertions = list(v)"),
        "cen.derivations_total": (
            "cen.ledger.spent_total", "cen.ledger.spent_total"),
        "cen.max_cut_depth": (
            "cen.ledger.max_cut_depth", "cen.ledger.max_cut_depth"),
        "cen.spent_this_turn": (
            "cen.ledger.spent_this_turn", "cen.ledger.spent_this_turn"),
        "cen.engine": ("RAW:cen.engine.dump()", "RAW:cen.engine.load(v)"),
        # the retrieval seat's working-set state (item 'retrieval'):
        # the C20 access-epoch table (RAM metadata, content-free) plus
        # the seat's own pricing flag.  The GETSPEC is conditional so a
        # seat-less state (the default) serializes a stable None — the
        # key is ALWAYS PRESENT (S10's shape gate requires exactly the
        # schema's keys), never silently dropped when the seat is off.
        "cen.retrieval": (
            "RAW:cen.retrieval.dump() if cen.retrieval is not None "
            "else None",
            "RAW:cen.retrieval.load(v) if (cen.retrieval is not None "
            "and v is not None) else None"),
        # the routing seat's state (R5, item 'extractor'): the WINDOW's
        # applied fraction (model state the next turn reads —
        # routing.RoutingWindow, whose `f` is the law's number for the
        # current consolidation window) plus the VERSION of the
        # externally-owned criterion in force.  Both are conditional-None
        # like cen.retrieval, so the key is ALWAYS PRESENT (S10's shape
        # gate requires exactly the schema's keys) and the default (no
        # selector attached) serializes a stable None.  The criterion's
        # BODY is never copied here: it is reloaded from its own anchored
        # store at a boundary.  The version rides along so a resume
        # cannot silently swap the criterion in force mid-window — a
        # mismatch REFUSES (fail-closed, the C8 discipline).
        "routing_window": ("RAW:self._routing_cp_get()",
                           "RAW:self._routing_cp_set(v)"),
        "routing_criterion": ("RAW:self._routing_crit_version()",
                              "RAW:self._routing_crit_set(v)"),
        # the COMMITMENTS seat's state (the self plan Q4): the open
        # commitment set plus the fulfilled/expired counters.  Conditional
        # -None like cen.retrieval / routing_window, so the key is ALWAYS
        # PRESENT (S10's shape gate) and the default (no self seat) is a
        # stable None; a mismatch between the checkpoint and the resume
        # config REFUSES rather than silently emptying the open set
        # (`_commitments_cp_set`, the fail-closed C8 discipline).
        "cen.commitments": ("RAW:self._commitments_cp_get()",
                            "RAW:self._commitments_cp_set(v)"),
        # THE ENCODING GATE'S POLICY (item 'encoding'): the INJECTED
        # policy's identity (policy_id + threshold + mode + tier +
        # enabled signals — the designer-visible shape, never the
        # mechanism's runtime), carried like the routing criterion's
        # VERSION: a resume into a config with a DIFFERENT policy
        # REFUSES rather than silently re-tiering mid-campaign (the
        # fail-closed C8 discipline; a checkpoint from a gate-less run
        # serializes a stable None, like cen.retrieval).
        "cen.encoding": ("RAW:self._encoding_cp_get()",
                         "RAW:self._encoding_cp_set(v)"),
        # the VOCATION layer's state (item 13): the selection record, the
        # gate's outcome log and the layer's own enabled flag — the state
        # the what-for line and the per-turn classification are read from.
        # Conditional-None like cen.retrieval / routing_window /
        # cen.commitments, so the key is ALWAYS PRESENT (S10's shape gate)
        # and a default run serializes a stable None; a mismatch between
        # the checkpoint and the resume config REFUSES rather than
        # silently dropping (or adopting) an expectation
        # (`_vocation_cp_set`, the fail-closed C8 discipline).
        "vocation": ("RAW:self._vocation_cp_get()",
                     "RAW:self._vocation_cp_set(v)"),
        # THE TOOL-CALL SEAT (the tool-call layer): the CEN's action
        # tracker (the registered-but-unanswered intents) plus the
        # harness-side ToolWorld (the completion ledger, the counters, the
        # ledger's history the reply is rendered from, and the ADMITTED SET
        # in force).  Conditional-None like cen.retrieval /
        # routing_window / cen.commitments / vocation, so the key is
        # ALWAYS PRESENT (S10's shape gate) and a default run serializes a
        # stable None; a mismatch between the checkpoint and the resume
        # config REFUSES rather than silently emptying the world
        # (`_actions_cp_set`, the fail-closed C8 discipline).
        "toolworld": ("RAW:self._actions_cp_get()",
                      "RAW:self._actions_cp_set(v)"),
        # THE REAL-TOOL SURFACE'S IDENTITY (worker prerequisite 3): the
        # declared targets + allowed tools + the counters — the seat's
        # callable surface, carried like the admissible set (a
        # construction parameter re-supplied by the caller).  The
        # SANDBOX and any background tasks are process state and are
        # NOT carried: a resume re-supplies the harness itself, and the
        # setter refuses a harness whose callable surface differs (what
        # is callable must not change mid-run).
        "tools_seat": ("RAW:self._tools_cp_get()",
                       "RAW:self._tools_cp_set(v)"),
        # THE MEMORY-CODEC SEAT'S POLICY IDENTITY (item 'codec'): the
        # INJECTED policy's policy_id ONLY — the designer-visible
        # shape, never the mechanism's runtime (the encoding gate's
        # `cen.encoding` precedent).  A checkpoint from a codec-less
        # run serializes a stable None; a resume into a config whose
        # injected policy disagrees REFUSES rather than silently
        # changing what the store's envelopes mean mid-campaign (C8
        # fail-closed, `_codec_cp_set`).
        "codec": ("RAW:self._codec_cp_get()",
                  "RAW:self._codec_cp_set(v)"),
        "record_path": ("record_path", "record_path"),
        "record_head": ("RAW:cen.record.head_hash", None),
        "record_count": ("RAW:cen.record.count", None),
    }

    #: checkpoint values whose INTERIOR the schema does not describe
    #: (they are opaque dicts/lists restored verbatim).  Their internal
    #: structure is guarded by the self-digest instead — the shape gate
    #: covers schema-described keys at every level, the digest covers
    #: what the schema cannot see into.
    _CP_OPAQUE: tuple = ("last_plant", "cen.queue", "cen.debt",
                         "cen.engine", "cen.retrieval", "routing_window",
                         "cen.commitments", "cen.encoding", "vocation",
                         "toolworld", "codec", "tools_seat")

    def to_checkpoint(self) -> dict:
        """Everything the next turn reads — the INTEGRATED state, BY
        CONSTRUCTION: walk _CP_SCHEMA and get every entry, then seal
        the OPAQUE values' interiors with a self-digest.  There is no
        second list; this method cannot forget a field the schema
        names, and S10 fails if the schema forgets a field the loop
        reads.  Together the shape gate (schema keys, every level) and
        the digest (opaque interiors) make ANY dropped key refuse the
        resume.  NOTE: this is drop/corruption detection for
        TRANSPORT, NOT an adversarial boundary — a forger recomputes a
        bare sha256; the adversarial boundary for durable state is the
        record's keyed anchor, not the checkpoint."""
        flat = {k: self._cp_get(spec)
                for k, (spec, _) in self._CP_SCHEMA.items()}
        out = self._nest(flat)
        opaque = {"turn": self.turn}
        for k in self._CP_OPAQUE:
            parts = k.split(".")
            node = out
            for pp in parts:
                node = node[pp]
            opaque[k] = node
        out["checkpoint_digest"] = hashlib.sha256(json.dumps(
            opaque, sort_keys=True, default=str).encode()).hexdigest()
        return out

    def _cp_get(self, spec: str):
        """Resolve a dotted attribute path relative to the STATE (the
        schema drops the `self.` prefix: "agent.G" -> self.agent.G)."""
        if spec.startswith("RAW:"):
            return eval(spec[4:], {"self": self, "cen": self.cen,
                                   "agent": self.agent})
        obj = self
        for part in spec.split("."):
            obj = getattr(obj, part)
        return obj

    def _cp_set(self, spec: str, value) -> None:
        if spec.startswith("RAW:"):
            exec(spec[4:], {"self": self, "cen": self.cen,
                            "agent": self.agent, "v": value})
            return
        parts = spec.split(".")
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    def _nest(self, flat: dict) -> dict:
        """Dotted schema keys -> the canonical nested layout:
        agent: {t, G, ..., sn: {a, S, g, monitor_cost}}, cen: {turn,
        queue, debt, ...}.  Pure structure: every value passes through
        untouched; only key placement changes."""
        out: dict = {}
        for k, v in flat.items():
            parts = k.split(".")
            node = out
            for pp in parts[:-1]:
                node = node.setdefault(pp, {})
            node[parts[-1]] = v
        return out

    @classmethod
    def from_checkpoint(cls, cp: dict, cfg: Stage2Config,
                        p: Params) -> "Stage2State":
        """Rebuild the INTEGRATED state THROUGH THE CONSTRUCTORS: fresh
        Agent, fresh CEN, then restore EVERY field the next turn reads
        by walking the SAME schema to_checkpoint used.  The walk is
        gated by _assert_shape: a checkpoint missing keys the schema
        names (a state field the next turn reads was dropped — the
        review-B1 failure) or carrying keys the schema does not know
        (an unknown format) is REFUSED before anything is applied.
        Fail-closed: no partial application, no silent defaults.  The
        durable record is re-opened from disk and chain-verified
        (DurableRecord.__init__ -> anchor.load -> _load -> verify ->
        _reconcile_anchor); a tampered record fails HERE, before any
        turn runs.  The engine is reloaded from its dumped facts."""
        st = cls(cfg, p, cp["record_path"])
        flat = _flatten_cp(cp)
        _assert_shape(cls._CP_SCHEMA, flat)
        # opaque-interior digest gate: the values the schema cannot see
        # into (last_plant's telemetry keys, the engine dump, queue,
        # debt) must arrive EXACTLY as to_checkpoint serialized them —
        # a dropped or added key inside an opaque value refuses the
        # resume.  Schema-described leaves are exempt: a checkpoint may
        # legitimately carry values a fresh run would not produce (S1
        # replays exactly that), and their integrity is the C9 record
        # cross-check's job, not the transport's.
        body = {k: flat[k] for k in cls._CP_OPAQUE}
        body["turn"] = flat["turn"]
        want = cp.get("checkpoint_digest")
        got = hashlib.sha256(json.dumps(body, sort_keys=True,
                                        default=str).encode()).hexdigest()
        if want is None or not hmac.compare_digest(want, got):
            raise ChainError(
                "checkpoint self-digest mismatch — an opaque value "
                "(last_plant / engine / queue / debt) was altered "
                "after writing; REFUSING the resume (C8/B1)")
        for k, (getspec, setspec) in cls._CP_SCHEMA.items():
            if setspec is not None:
                st._cp_set(setspec, flat[k])
        # C9 cross-check: the record on disk must verify AND its head
        # must equal the checkpoint's (an append-only file that grew is
        # fine — its prefix is intact; a changed prefix is not)
        if st.cen.record.count < flat["record_count"]:
            raise ChainError("durable record SHRANK — decisions lost (C9)")
        if st.cen.record.head_hash != flat["record_head"]:
            raise ChainError(
                "record head moved between checkpoint and resume — "
                "only appends were allowed (C9)")
        return st


def _flatten_cp(cp: dict) -> dict:
    """Nested v1 layout -> the schema's flat dotted keys.  The inverse
    of Stage2State._nest; shape mismatches raise KeyError (fail-closed
    at the gate) rather than being papered over."""
    flat: dict = {}
    for top, v in cp.items():
        if top == "checkpoint_digest":
            continue       # the self-digest, verified separately
        if top == "agent":
            for k2, v2 in v.items():
                if k2 == "sn":
                    for k3, v3 in v2.items():
                        flat[f"agent.sn.{k3}"] = v3
                else:
                    flat[f"agent.{k2}"] = v2
        elif top == "cen":
            for k2, v2 in v.items():
                flat[f"cen.{k2}"] = v2
        else:
            flat[top] = v
    return flat


def _assert_shape(schema: dict, flat: dict) -> None:
    """Fail-closed structural gate: the flattened checkpoint must carry
    exactly the schema's keys.  Missing = a field the next turn reads
    was dropped from the checkpoint (review B1); extra = an unknown
    format.  Both REFUSE the resume — never a silent default."""
    sk, fk = set(schema), set(flat)
    missing = sorted(sk - fk)
    extra = sorted(fk - sk)
    if missing:
        raise KeyError(
            f"checkpoint is missing state keys the next turn reads: "
            f"{missing} — REFUSING the resume (C8/B1: the checkpoint "
            f"surface must cover the whole read surface)")
    if extra:
        raise KeyError(
            f"checkpoint carries keys unknown to the schema: {extra} "
            f"— REFUSING the resume (unknown format)")


def _queue_to_cp(b: AssertionBatch) -> dict:
    return {"turn": b.turn,
            "assertions": [{"id": a.assertion_id, "le": a.le_text,
                            "terms": list(a.terms)}
                           for a in b.assertions],
            "proposals": [{"id": pr.lever_id, "val": pr.new_value,
                           "reason": pr.reason}
                          for pr in b.proposals],
            "self_content": b.self_content,
            "commitments": [{"id": c.commitment_id, "le": c.le_text,
                             "terms": list(c.terms), "turn": c.turn,
                             "deadline": c.deadline}
                            for c in b.commitments]}


def _batch_from_cp(b: dict) -> AssertionBatch:
    from cen import Commitment
    return AssertionBatch(
        turn=b["turn"],
        assertions=tuple(
            Assertion(a["id"], a["le"], tuple(a["terms"]))
            for a in b["assertions"]),
        proposals=tuple(
            LeverProposal(pr["id"], pr["val"], pr["reason"])
            for pr in b["proposals"]),
        self_content=b["self_content"],
        commitments=tuple(
            Commitment(c["id"], c["le"], tuple(c["terms"]),
                       int(c["turn"]), float(c["deadline"]))
            for c in b.get("commitments", ())))


def checkpoint_read_surface() -> set:
    """The canonical C8 read surface: every state attribute the turn
    loop and the next DMN turn read, derived from _CP_SCHEMA — the
    same single source of truth to_checkpoint/from_checkpoint walk —
    plus the reasoned exclusions (construction parameters and outputs
    that are NOT serialized state; see _CP_SCHEMA's docstring).  S10
    cross-checks this against an independent AST enumeration of what
    run_stage2 actually reads, so neither list can silently rot."""
    keys = set(Stage2State._CP_SCHEMA)
    return keys


def _tmp_record_path(cfg: Stage2Config) -> str:
    if cfg.record_path:
        return cfg.record_path
    d = tempfile.mkdtemp(prefix="stage2-record-")
    return os.path.join(d, "DECISIONS.jsonl")


def _inward_of(dmn, stream: str, prose: str) -> float:
    """THIS TURN'S INWARD SHARE, on the EMITTER'S OWN instrument.

    THE TRACE IS PRIMARY: a generator that exposes the model's two
    streams (`last_inward` — `dmn_llm`'s chat path, `message.thinking`
    against `message.content`) is measured with
    `selfmodel.inward_share_trace`, the naming S2 asked for
    (self-directed vs task-directed).  A generator with no separate
    inward channel (`last_inward` absent or None — the `/api/generate`
    path, every fixture, the stub) FALLS BACK to `selfmodel.inward_share`,
    the pre-trace prose/stream share, so those arms are unchanged and stay
    comparable.  One place decides this, so the two instruments cannot be
    mixed silently mid-run.

    THE PROTOCOL'S TWO DISTINCT ABSENCES (the review's S1; see
    `dmn_llm._parse_chat`): `None` (or the attribute missing) means THIS
    EMITTER HAS NO INWARD CHANNEL — a declared property of the
    `/api/generate` path, answered with the labelled fallback.  A STRING
    means the emitter HAS the channel, and `""` is then a MEASUREMENT:
    the turn came out entirely outward, inward share EXACTLY 0.0.  A
    TRACE THAT IS ABSENT ON THE WIRE IS NEITHER — it is a
    transport/template fact, and the chat parse REFUSES the turn rather
    than coercing it to `""` (a missing field would otherwise be scored
    as "the agent never turned inward")."""
    from selfmodel import inward_share, inward_share_trace
    inward = getattr(dmn, "last_inward", None)
    if isinstance(inward, str):
        return inward_share_trace(inward, stream)
    return inward_share(stream, prose)


def _universe_of(dmn, turn: int):
    """THE TASK UNIVERSE THE EMITTER WAS HANDED THIS TURN, or None when
    it is UNDEFINED (item 13's vocation-directed observable).

    TWO SOURCES, both the emitter's OWN, in order:

      * `last_universe` — the DECLARED protocol for an emitter that keeps
        the universe it rendered (the `last_inward` convention: an
        attribute on the callable the harness was given).  Read verbatim
        when present.
      * `world` — `dmn_llm.LLM_DMN` holds the `TaskWorld` it renders
        (`self.world`), and `TaskWorld.step(turn)` is PURE in
        `(seed, turn)` (dmn_llm.py:343-352: "a fresh TaskWorld(seed)
        reproduces the identical state, and the SAME object can both
        render the prompt AND supply the universe the fabricated-arg
        metric is measured against").  Re-stepping the emitter's OWN
        world at the SAME turn therefore returns exactly the universe
        that turn's prompt named: the SAME SOURCE, not a re-derivation.

    ANYTHING ELSE (a fixture, `stream_to_batch`'s wrapper, a custom
    emitter that renders no TaskWorld, a wrapper that swallows both
    attributes) -> None, and the classification reports `share=None` with
    `n` LOGGED.  An absent universe is UNDEFINED, NOT ZERO: a fabricated
    0.0 would say "it emitted no direction", which is a different and
    false claim (the `_inward_of` convention for a batch emitter).  The
    fix for an emitter that wants the observable is to expose
    `last_universe`; the harness never guesses a universe, and never
    re-derives one from the prompt text."""
    uni = getattr(dmn, "last_universe", None)
    if uni is not None:
        return frozenset(str(x) for x in uni)
    world = getattr(dmn, "world", None)
    step = getattr(world, "step", None)
    if callable(step):
        return frozenset(str(x) for x in step(int(turn))[1])
    return None


def _guard_resume_drive(st: Stage2State, sch: Schedule) -> None:
    """C8, FAIL-CLOSED — THE a_hold DRIVE IS PLANT STATE AND IT LIVES IN
    THE CALLER'S SCHEDULE, SO A RESUME MUST CARRY IT.

    The drive is written onto the caller's seat
    (`SelfReferentialDrive.set_drive`) at each consolidation boundary.  On
    a resume the harness REBUILDS every piece of state from the
    checkpoint, but the schedule is a CONSTRUCTION PARAMETER, re-supplied
    by the caller like `cfg.dmn` or the routing selector — so a caller
    restarting the process hands over a FRESH seat whose drive is 0.0
    while `st.self_drive` (carried by `_CP_SCHEMA`) holds the window's
    real value.  The plant then runs the rest of the window UNDRIVEN and a
    collapse experiment silently un-collapses [MEASURED,
    /tmp/selfrev_resume.py: the uninterrupted run holds G 0.2896 ->
    0.2899 while the resume recovers to 0.8730].

    REFUSED, NOT SILENTLY RE-APPLIED, because the harness cannot
    distinguish a fresh process that FORGOT the seat from a caller who
    deliberately supplies a different drive: re-writing the state field
    onto caller-supplied state would be a silent override of the caller's
    own plant input (the class this project refuses everywhere).  It is
    also the discipline already in force at this seam — the commitments
    mismatch REFUSES both ways (`_commitments_cp_set`) and a criterion
    that moved REFUSES (`_routing_crit_set`).  Both ways out are named in
    the message.

    WHAT THE GUARD READS, STATED SO IT IS NOT OVER-CLAIMED (review nit,
    `handoff-selfreg-repoint-review-result` finding 3): it compares the
    seat's `drive` against the checkpoint's `st.self_drive` — ONE of the
    three numbers that compose the effective hold (a_hold = clip(base +
    gain*drive), `selfmodel.SelfReferentialDrive.value`).  The BASE
    schedule and the GAIN are the caller's own plant input, re-supplied
    at construction like `cfg.dmn`, and the harness has no record of them
    to audit (a plain `Schedule(channels={'a_hold': [[0, 1e9, 0.9]]})`
    is equally unauditable) — so a resume may compose a DIFFERENT
    effective a_hold while carrying the same drive.  That is the caller's
    trust boundary, the same one every other construction parameter sits
    on, stated rather than silently assumed away."""
    if not hasattr(sch, "set_drive"):
        return          # no seat: this arm never gave the drive a path
    have = float(getattr(sch, "drive", 0.0))
    want = float(getattr(st, "self_drive", 0.0))
    if abs(have - want) > 1e-12:
        raise ChainError(
            f"resume drive mismatch: the re-supplied schedule carries "
            f"drive={have!r} but the checkpoint's state says the window's "
            f"drive is {want!r} (st.self_drive) — the plant would run the "
            f"rest of the window under a drive the checkpoint did not "
            f"have, and a resumed collapse run would silently un-collapse "
            f"(C8, fail-closed).  REFUSING the resume.  Ways out: call "
            f"sch.set_drive(resume_state.self_drive, resume_state.turn) "
            f"before resuming — or resume with a schedule that has no "
            f"drive seat (a plain Schedule) if the drive is not part of "
            f"this arm.")


def run_stage2(sch: Schedule, turns: int, cfg: Stage2Config | None = None,
               p: Params | None = None,
               checkpoint_fn: Callable | None = None,
               resume: Stage2State | None = None) -> Stage2State:
    """Run `turns` DMN turns.  One turn = one CEN txn + one plant step.
    checkpoint_fn(turn, state) may stop the run early (return False);
    the state it saw IS the checkpoint object (part S2's test hook).
    `resume`: continue a prior state — the C8 path.  Returns the state
    (its .log is the per-turn record; the STATE, not the log, is the
    integration)."""
    cfg = cfg or Stage2Config()
    p = p if p is not None else Params()
    # THE SELF SEAT'S BUILD-TIME CONSTANTS.  `_bb_kw` is the keyword set
    # every `build_batch` call gets when the self seat is on (the extended
    # declared predicate set — `expect` becomes a valid span — plus the
    # commitment split and the horizon T); EMPTY otherwise, so every
    # default call is the pre-self call, byte for byte.  `_self_on` gates
    # the per-window wiring below.
    _self_on = cfg.self_T is not None
    # THE DRIVE'S OWN EXISTENCE (A3).  `_drive_on` is the gate on the inward
    # accumulator: with the self seat on it is the self seat's instrument
    # (unchanged); with `drive_seat` on and the self seat OFF it is the
    # decoupled arm's — the same accumulator feeding the same seat, with no
    # self-description anywhere in the prompt.  Both off (the default) =
    # nothing accumulates, i.e. today's bytes.
    _drive_on = _self_on or cfg.drive_seat
    # THE MEASUREMENT'S OWN GATE (one seat over from the drive's): the
    # per-turn inward share is computed whenever SOMETHING reads it — the
    # drive's accumulator or the log column an unwired baseline needs
    # (`inward_seat`).  It is a MEASUREMENT gate only: the accumulation and
    # the `set_drive` write below stay exactly where `_drive_on` and the
    # self seat put them.
    _measure_inward = _drive_on or cfg.inward_seat
    # TWO CONFIGS THAT NAME A WRITE WITH NO SEAT TO HOLD IT are REFUSED
    # here rather than run inert (the declared-but-never-read defect, the
    # `vocation.VocationConfig.reselect` precedent — and the F5 class
    # itself, which was a drive that LOOKED wired and could not write: an
    # inert drive reads downstream as "no collapse").
    if cfg.drive_seat and not hasattr(sch, "set_drive"):
        raise ChainError(
            "cfg.drive_seat=True with a schedule that exposes no "
            "`set_drive`: the switch names the per-window a_hold write and "
            "this seat cannot receive it, so the arm would accumulate an "
            "inward share, LOG it (`st.self_drive`) and never reach the "
            "plant — an inert drive reads as 'no collapse' and would be "
            "scored as one.  REFUSING.  Ways out: wrap the schedule in "
            "`selfmodel.SelfReferentialDrive(base, gain=1.0)` — or leave "
            "drive_seat False if this arm is not the wired one.")
    if cfg.action_source is not None and not cfg.actions:
        raise ChainError(
            "cfg.action_source is set but cfg.actions is False: nothing "
            "would construct a ToolWorld to read the source, so the "
            "worksheet it names could never be adjudicated (a switch "
            "nothing reads).  REFUSING.  Ways out: set actions=True with "
            "action_admissible naming the action predicates — or drop the "
            "source.")
    if cfg.world_echo_window is not None and not cfg.actions:
        raise ChainError(
            "cfg.world_echo_window is set but cfg.actions is False: no "
            "ToolWorld would exist to render the ledger, so the window "
            "is a switch nothing reads.  REFUSING.  Ways out: set "
            "actions=True — or drop the window.")
    if cfg.tools is not None and not cfg.actions:
        raise ChainError(
            "cfg.tools is set but cfg.actions is False: the tool surface "
            "answers on the state channel through the action seat's "
            "ToolWorld (`ToolWorld.render`), so a tool harness with no "
            "world is a switch whose answers have no carrier.  REFUSING.  "
            "Ways out: set actions=True so the world exists — or drop the "
            "harness (the default, byte-identical to the pre-tools loop).")
    _bb_kw: dict = {}
    if _self_on:
        from selfmodel import COMMITMENT_PREDICATES, SELF_PREDICATES
        _bb_kw = {"predicates": dict(SELF_PREDICATES),
                  "commitment_predicates": COMMITMENT_PREDICATES,
                  "horizon": float(cfg.self_T)}
    if resume is not None:
        st = resume
        # THE ONE PIECE OF PLANT STATE THAT LIVES IN A CONSTRUCTION
        # PARAMETER: refuse a resume whose re-supplied seat disagrees with
        # the checkpoint (C8, fail-closed — see `_guard_resume_drive`).
        _guard_resume_drive(st, sch)
    else:
        st = Stage2State(cfg, p, _tmp_record_path(cfg))
    # THE ACTION GRAMMAR (the tool-call layer).  The fourth channel is
    # admitted ONLY for the predicates the CALLER's admissible set names —
    # the world's own gate (EXTERNALLY OWNED, default EMPTY) — so with an
    # empty set NO predicate is added, no span routes to the actions
    # channel, and the split is byte-identical to the seat being off.  The
    # declared set is the action grammar's own base
    # (`actions.ACTION_DECLARED_PREDICATES` = the extractor's set PLUS
    # `complete`), merged with the self seat's set when both are on, so
    # the two seats compose instead of one overwriting the other.
    if st.toolworld is not None and st.toolworld.admissible.predicates:
        from actions import ACTION_DECLARED_PREDICATES
        _admitted = st.toolworld.admissible.predicates
        preds = dict(_bb_kw.get("predicates") or ACTION_DECLARED_PREDICATES)
        preds.update({q: 1 for q in _admitted})
        _bb_kw["predicates"] = preds
        _bb_kw["action_predicates"] = _admitted
    for turn in range(st.turn + 1, st.turn + 1 + turns):
        routed = 0
        emitted_stream = None
        prose = ""
        talking_bytes = 0
        talking_actions = 0
        talking_applied = 0
        talking_refused = 0
        talking_applied_ids = ()
        inward_share = None
        _is_boundary = False
        # THE SELF'S CONSOLIDATION BOUNDARY (§11d's self subsection).
        # INDEPENDENT of the routing seat: the self block, the
        # model-of-itself and the a_hold drive are all set ONCE here and
        # held for the window's turns.  `is_self_boundary` is False
        # whenever the self seat is off (self_T None), so the default
        # loop is byte-identical.
        is_self_boundary = st.self_window_due(turn)
        if is_self_boundary:
            st.self_window_boundary(turn, sch)
        # THE DRIVE'S OWN BOUNDARY (A3 — the F5 decoupling).  A SEPARATE,
        # INDEPENDENT window, on the same tau_S timescale, for the arm whose
        # emitter has an inward channel but is handed no self-description:
        # `self_T=None` + `drive_seat=True`.  Two features of the placement
        # are the change's whole content:
        #   * it is NOT inside `self_window_boundary`, which returns early
        #     when the self seat is off (before this, the drive was dead in
        #     exactly the arm the corrected experiment's control needs); and
        #   * the due-predicate is False whenever the self seat IS on, so
        #     there is exactly ONE `set_drive` per window and the self arm's
        #     behaviour is unchanged — a suppression, not a second write.
        # The predicate is False on the default path, so the loop's bytes
        # for every pre-existing config are untouched.
        if st.drive_window_due(turn):
            st.drive_window_boundary(turn, sch)
        # THE MEMORY'S CONSOLIDATION BOUNDARY (item 'retrieval' / C20) —
        # the THIRD, INDEPENDENT window, and the ONLY caller of
        # `AccessEpochs.consolidate()` on the run path.  Placed HERE, at
        # the top of the turn, for the same reason the self's boundary is:
        # the boundary OPENS the window, so every retrieval in it records
        # at the new epoch and the window is one decay step wide.  It is
        # deliberately OUTSIDE the routing block below and OUTSIDE
        # `self_window_boundary` (which returns early when self_T is None):
        # the retrieval seat is attached whenever `retrieval_priced or
        # retrieval_decay != 1.0`, with neither the self nor the routing
        # seat necessarily present, and a boundary nested in either would
        # silently leave C20's decay unscheduled in exactly those arms —
        # the defect this wiring exists to close.  The predicate is False
        # when no seat is attached, so the default loop is untouched.
        if st.memory_window_due(turn):
            st.memory_window_boundary(turn)
        # the DMN's per-turn context, built ONCE: the cross-boundary plant
        # snapshot PLUS the reconstructed self (the previous turn's
        # RetrievalOutcome.reconstruction.text, stashed by check_turn's
        # caller below).  One dict for both call sites, so they cannot
        # drift.
        #
        # THE INJECTED BLOCK IS PER-WINDOW, THE CHARGE PER-TURN (§11c's
        # reconciliation, stated): with the self seat ON, the generator is
        # handed the WINDOW's block (`st.self_block` — window 1 the base
        # self, later windows the boundary's reconstruction) and the
        # model-of-itself, NOT the per-turn reconstruction; with the seat
        # OFF (the default) the context is EXACTLY the pre-self one,
        # `retrieved_self = st.dmn_self` (the per-turn, priced
        # reconstruction), so the default bytes are unchanged.
        dmn_ctx = {**st.last_plant, "retrieved_self": st.dmn_self}
        if st.cfg.self_T is not None:
            # ---- THE SELF SEAT, RE-THOUGHT (2026-09-29) ----------------
            # TWO RULES, both required, both MEASURED as necessary on a
            # live probe:
            #
            # (1) THE REFRESH IS TRIGGERED BY COMPACTION, NOT BY THE
            #     SELF WINDOW.  The arm variable is "who restores the self
            #     AFTER A COMPACTION", and compactions (every ~10 turns)
            #     are an order of magnitude more frequent than the
            #     self-consolidation window (self_T = 100 turns).  Tied to
            #     the window, the arm did nothing at all in a 40-turn run:
            #     MEASURED, no boundary fired and both arms carried the
            #     identical seed for the whole probe.
            # (2) THE BLOCK IS SPENT ON ONE TURN.  It enters the
            #     conversation on the turn it is (re)generated and is then
            #     cleared, so the derivation lives in the memory as
            #     ORDINARY CONTENT and compaction can actually remove it.
            #     Re-spending it every turn put the seed into every prompt
            #     (MEASURED: turn 1 3,834 chars including the 1,007-char
            #     seed), so the next turn undid every compaction and the
            #     loss read 0.0 forever -- campaign 3's defect in a new
            #     costume.
            _mem = None
            _inner = getattr(st.cfg.dmn, "inner", None) or st.cfg.dmn
            _mem = getattr(_inner, "memory", None)
            _ncomp = len(getattr(_mem, "compactions", ()) or ())
            if _ncomp > getattr(st, "_comps_seen", 0):
                # a compaction has happened since the last (re)generation
                st._comps_seen = _ncomp
                st.self_block = st._regenerate_self_block()
                # WHAT THE ARM ACTUALLY PRODUCED, kept for the record: the
                # inject arm's is the seed again; the reconstruct arm's is
                # the AGENT'S OWN answer, and it is the DV's raw input.
                st.last_reconstruction = st.self_block
                st.last_reconstruction_turn = turn
            dmn_ctx = {**st.last_plant, "retrieved_self": st.self_block,
                       "self_model": st.self_model_block}
            st.self_block = ""      # spent: rule (2)
        if st.toolworld is not None:
            # THE WORLD'S REPLY (the tool-call layer).  The harness-side
            # ToolWorld renders the completion ledger and the PREVIOUS
            # turn's typed refusals — the environment speaking, exactly as
            # the plant snapshot does — on the EXISTING state-block channel
            # (`dmn_ctx`), so no new channel is invented (the key is new,
            # the channel is the one the environment already talks on).
            # A tool result is the WORLD's content, never the agent's: it
            # is not written to the store and not published as
            # `self_content`.  Whether the emitter RENDERS it is the
            # emitter's business (the plan's risk (b)): a fixture that
            # ignores the state block will not observe effects.
            #
            # THE OPEN SET RIDES THE SAME LINE (A1(ii)'s 'open' semantics),
            # and ONLY when a source is bound: without one the world cannot
            # know what was offered on earlier turns, so it says nothing —
            # and the bytes of every pre-change fixture are untouched.
            # The worksheet the prompt names and the universe the world
            # ADJUDICATES against are then one source (`offered()` below),
            # which is what forbids the class of defect where the prompt
            # offers a task the world refuses.
            _ws = st.toolworld.render(st.turn,
                                      tool_results=(
                                          cfg.tools.render_reply()
                                          if cfg.tools is not None else ""))
            _open = st.toolworld.render_open(st.turn)
            dmn_ctx["tool_state"] = (f"{_ws}\n{_open}" if _open else _ws)
        if st.routing_window is not None:
            w = st.routing_window
            # CONSOLIDATION BOUNDARY (R2's timescale: tau_S = TAU_S_TURNS
            # = 100 t.u.; one turn = one tau_a step, the F4 convention):
            # set THIS window's f by the law and RELOAD the
            # externally-owned criterion.  w.windows == 0 is the first
            # turn of a fresh state — turn 0 is a boundary too, and the
            # window must run under the LAW's number from its first turn,
            # not under RoutingWindow's dataclass default.
            _is_boundary = (w.windows == 0 or turn % TAU_S_TURNS == 0)
            if _is_boundary:
                # THE D-ANALOGUE IS BUILT FROM THE PLANT'S OWN DRIVE
                # INPUTS: its addend is the SAME B the plant's D was
                # actually driven with — `st.p2_addend`, the plant's own
                # logged edge_addend = EMA_tauD(c) when the coupling is on
                # and 0.0 when it is off (the model's ONE c; the OFF arm
                # carries no addend at all) — paired with the schedule's
                # own 'A'.  A router gating on a different quantity than
                # its substrate uses is the thetafix-class defect, so the
                # CEN's measured u/n (telemetry, `st.backlog_rate`) is NOT
                # used here.
                # G=None (the DEFAULT): the G-analogue is UNSOLVED (§9),
                # so the law returns the maximally conservative arm with
                # the fact recorded ('g_unsolved_conservative_arm');
                # fabricating a G here would be the standing-order
                # violation.  cfg.agent_g=True CLOSES that seat with the
                # AGENT'S OWN measured quantity — `st.coverage`,
                # `Reconstruction.coverage`, the last turn's priced
                # reconstruction's coverage — a SUPPLEMENT to the plant's
                # frozen G, never a replacement (the plan's Q3), so a
                # collapse can be the AGENT's while the plant recovers.
                # The mapping is ORDINAL: the model's G is a continuous
                # depletable scalar, this is a per-turn fraction in [0,1];
                # shapes and orderings, never values (architecture.md
                # :195).  S is the plant's own setpoint state.  The law's
                # ARMING LEVEL is the substrate's own actual one
                # (Theta*S/S_rest, floorless in this plant), wired at
                # window construction.
                w.consolidate(backlog_ema=st.p2_addend,
                              G=(st.coverage if cfg.agent_g else None),
                              S=st.agent.sn.S,
                              A=sch.value("A", st.agent.t))
                st.reload_criterion()
            from interleave import build_batch
            stream = st.dmn(turn, dmn_ctx)
            if not isinstance(stream, str):
                raise ChainError(
                    f"routing is ON but the DMN emitted "
                    f"{type(stream).__name__}, not the free-form stream: "
                    f"with routing enabled the EXTRACTOR — not the DMN — "
                    f"decides what is a claim (R5: the generator must not "
                    f"control the split), so the DMN must emit its raw "
                    f"stream")
            selected, _ex = st.plan_routing(turn, stream,
                                            boundary=_is_boundary)
            batch, _ex2 = build_batch(turn, stream, selected=selected,
                                      **_bb_kw)
            routed = len(selected)
            emitted_stream, prose = stream, _ex2.self_content
            # THE REAL-TOOL SURFACE (worker prerequisite 3): parse the
            # emitted stream's fenced tool blocks and RUN them in the
            # designer-constructed sandbox.  Placement: AFTER the batch
            # build (the blocks are prose on the span channel — they are
            # not claims and must not affect the split) and BEFORE
            # submit/check (the tool answer is the WORLD's content, not
            # the agent's).  NEVER raises on the tool's own failures: a
            # malformed block or a refused call is a TYPED record the
            # next turn renders back.
            if cfg.tools is not None:
                cfg.tools.apply_turn(turn,
                                     parse_tool_blocks(stream).blocks)
        else:
            # ROUTING OFF = NO SELECTOR = ROUTE-ALL — a SUPPORTED, STATED
            # mode, not a fallback.  Without a selector there is nothing
            # that decides the split, so EVERY valid span routes (f == 1,
            # `selected=None`) and the prose is persisted byte-exact;
            # that is byte-identical to the pre-routing (Stage-1) loop,
            # and it is the mode the pre-registered agent experiment's
            # 'direct replica of exp22' arm REQUIRES (handoff-selfreg-
            # agentexp-plan) — so a stream-emitting DMN is ACCEPTED here
            # and the mode is stated rather than refused (§1a: do not
            # delete the arm to make the wiring easier).  The ROUTING-ON
            # branch above is the other mode: the injected selector
            # decides, and the DMN must hand over its raw stream.
            emitted = st.dmn(turn, dmn_ctx)
            if isinstance(emitted, str):
                from interleave import build_batch
                batch, _ex = build_batch(turn, emitted, selected=None,
                                         **_bb_kw)
                emitted_stream, prose = emitted, _ex.self_content
                # THE REAL-TOOL SURFACE (worker prerequisite 3), the
                # routing-OFF twin of the site above: the blocks ride the
                # stream, the span split is untouched, the world answers.
                if cfg.tools is not None:
                    cfg.tools.apply_turn(turn,
                                         parse_tool_blocks(emitted).blocks)
            elif isinstance(emitted, AssertionBatch):
                batch = emitted
                # THE TRACE PROTOCOL IS NOT DROPPED FOR A BATCH EMITTER
                # (the review's S2, `handoff-selfreg-repoint-review-result`
                # finding 4(iv)).  `dmn_llm.stream_to_batch` — the
                # documented way to hand a chat emitter to this branch —
                # carries the RAW emission and the extracted prose beside
                # the trace (`last_stream`/`last_prose`), so a
                # trace-bearing batch emitter is weighed EXACTLY as a raw
                # `str` emitter is, with the same `_inward_of`.  Gated on
                # a REAL trace (`last_inward` a str): a bare
                # `AssertionBatch` from a generator with no inward channel
                # is left as it was — the drive is UNDEFINED there, not
                # zero, and inventing a zero would look like "a
                # non-self-referential generator" when it is only "a
                # generator that emits batches".  MEASURED before the fix:
                # a 120-turn wrapped-emitter run accumulated
                # self_inward_n = 0 and the drive stayed 0.0.
                raw = getattr(st.dmn, "last_stream", None)
                if isinstance(raw, str) and isinstance(
                        getattr(st.dmn, "last_inward", None), str):
                    emitted_stream = raw
                    prose = getattr(st.dmn, "last_prose", "") or ""
            else:
                raise ChainError(
                    f"routing is OFF (no routing_selector is injected) and "
                    f"the DMN emitted {type(emitted).__name__}, which is "
                    f"neither the free-form stream (str) nor an "
                    f"AssertionBatch: with routing OFF every valid span "
                    f"routes (route-all), so emit the raw stream — or wrap "
                    f"the DMN with dmn_llm.stream_to_batch")
        # THE AUTOMATIC SEAT'S CONTEXT (assoc.py): the CURRENT turn's
        # emission, handed to the seat by the LOOP (the caller) — never
        # taken by the mechanism — so the cue is a function of what the
        # agent is emitting NOW (its self content plus its claims' LE
        # text).  The seat's retrieve() inside check_turn below consumes
        # it; the reconstruction informs the NEXT turn's context through
        # st.dmn_self, exactly as the priced seat's does.  The priced
        # seat exposes no note_context, so this is a no-op there — one
        # guarded line, no second branch to drift.
        if hasattr(st.retrieval, "note_context"):
            st.retrieval.note_context(batch)
        st.cen.submit_batch(batch)
        backlog_before = st.cen.backlog_outstanding()
        tr = st.cen.check_turn(batch)
        # THE WORLD APPLIES (the tool-call layer).  The CEN REGISTERED the
        # turn's admissible intents and emitted them on `tr.talking`; the
        # HARNESS — the world — applies them to its OWN bookkeeping and
        # answers with TYPED effect records (applied / refused+reason).  NO
        # PLANT EDGE: the frozen model has no action input (dpdr/model.py:
        # 107-124), and the answer is attached to the emission the CEN
        # produced (the CEN could never know it — that is the seam) and
        # handed back to the CEN's tracker, which counts it.
        if tr.talking is not None:
            from actions import render_talking
            # THE ADJUDICATION UNIVERSE.  With a source bound (A1) it is the
            # world's OWN offered set: the current turn's draw UNION every id
            # it has told the agent is open and the agent has not completed —
            # ONE source with the worksheet the prompt renders.  Without a
            # source it is `_universe_of` exactly as before (the emitter's
            # own TaskWorld re-stepped), so every pre-change fixture keeps
            # its behaviour, including the `universe_undefined` refusal for a
            # wrapper that exposes no universe.
            _uni = (st.toolworld.offered(turn) if st.toolworld.has_source
                    else _universe_of(st.dmn, turn))
            _rep = st.toolworld.apply(turn, tr.talking.actions,
                                      universe=_uni)
            tr.talking.effects = _rep.applied + _rep.refused
            st.cen.actions.resolve(_rep)
            talking_actions = len(tr.talking.actions)
            talking_applied = len(_rep.applied)
            talking_refused = len(_rep.refused)
            # THE PER-ID LEDGER (one source): the applied targets in the
            # world's answer order, and their classes READ FROM THE
            # SOURCE's own census (`class_of`), never re-derived from the
            # id's bytes.  A source with no census (a bare callable, the
            # TaskWorld regime) records None per id: the class is a fact
            # the world did not state, and the honest row says so rather
            # than guessing.
            talking_applied_ids = tuple(str(e.target)
                                        for e in _rep.applied)
            _cls = getattr(st.toolworld.source, "class_of", None)
            talking_applied_classes = tuple(
                (None if not callable(_cls) else _cls(str(e.target)))
                for e in _rep.applied)
            talking_bytes = len(render_talking(tr.talking))
        # the reconstruction's ONLY consumer (retrieval.py's
        # Reconstruction.text, §11c): the NEXT turn's DMN context.
        # Retrieval stays PRICED — the charge happened FIRST, inside
        # check_turn — so this hop is the wiring, never a free
        # side-channel that would make G non-depletable.
        st.dmn_self = (tr.retrieval.reconstruction.text
                       if tr.retrieval is not None else "")
        # THE AGENT-G OBSERVABLE AND THE INWARD ACCUMULATOR.  Coverage is
        # `Reconstruction.coverage` — READ, never recomputed (one source,
        # or the law and the measurement drift).  The inward share is this
        # turn's contribution to the window's a_hold drive; it is measured
        # only when a STREAM was emitted (a batch-emitting DMN has no
        # prose to weigh: the drive is undefined rather than zero, and
        # inventing a zero would look like 'a non-self-referential
        # generator' when it is only 'a generator that emits batches').
        if tr.retrieval is not None:
            st.coverage = float(tr.retrieval.reconstruction.coverage)
            st.recon_candidates = int(tr.retrieval.reconstruction.candidates)
        # THE RETRIEVAL MAINTENANCE CHARGE, exposed as STATE (the
        # long-horizon experiment's cost term — one source, READ off the
        # C11 surface's own per-turn outcome, never recomputed from the
        # store): `RetrievalOutcome.derivations` is the C11 charge the
        # seat billed for this turn's reconstruction of the self.  It is
        # a MEASUREMENT seat — the model's prediction is computed FROM it
        # post hoc; feeding the plant with it is what the killed rig did
        # and nothing here does (the plant runs the caller's schedule,
        # untouched).  0 when no retrieval seat is attached, which is a
        # fact about the arm, not a zero charge.
        st.retrieval_derivations = (0 if tr.retrieval is None
                                    else int(tr.retrieval.derivations))
        # SELECTIVE ENCODING'S OBSERVABLES (item 'encoding'): read off
        # the turn's OWN GateOutcome, never recomputed — one source
        # (the retrieval_derivations convention).  Inert defaults with
        # no gate attached, so the default log rows are byte-identical.
        if tr.encoding is not None:
            st.encode_salience = float(tr.encoding.salience)
            st.encode_admitted = int(1 if tr.encoding.admitted else 0)
            if not tr.encoding.admitted:
                st.encode_denied += 1
        if _measure_inward and emitted_stream is not None:
            # THE TRACE IS PRIMARY when the emitter has one (`_inward_of`:
            # `inward_share_trace`, the model's own two streams); the
            # pre-trace prose/stream share is the fallback for the
            # /api/generate path and for every fixture.
            #
            # `_drive_on` IS `_self_on OR cfg.drive_seat` (A3): the ONE
            # instrument feeds the ONE accumulator in both arms, so the arm
            # without the self-description cannot be measuring a different
            # quantity than the arm with it.  With both switches off this is
            # `_self_on` and the default path is unchanged.
            _ish = _inward_of(st.dmn, emitted_stream, prose)
            inward_share = _ish
            if _drive_on:
                st.self_inward_sum += _ish
                st.self_inward_n += 1
        st._sync_commitment_observables()
        # THE VOCATION-DIRECTED OBSERVABLE (item 13, plan Q3 (2)), per turn
        # and CEN-side: this turn's commitments, classified against the
        # task universe the emitter was ACTUALLY handed.  A commitment
        # aimed PAST the offered work is a DIRECTION; one about work
        # already offered is a REPORT.  Deterministic, LLM-free, ONE
        # universe source (`_universe_of`): with the emitter rendering no
        # TaskWorld the report is UNDEFINED (share None, n logged) — never
        # a fabricated 0.0.  The layer off leaves `vrep` None and the log
        # columns at their inert defaults.
        vrep = None
        if st.vocation is not None:
            from vocation import classify_directed
            vrep = classify_directed(turn, _universe_of(st.dmn, turn),
                                     batch.commitments)
        st._advance_backlog_ema(backlog_before)
        # TELEMETRY, MEASURED FROM THE SUBSTRATE (never proxied): u/n, the
        # share of this turn's assertions that accrued UNCHECKED.  It is
        # the CEN's real reading of the model's c-quantity, and it DRIVES
        # NOTHING — the model has ONE c (the plant's switch state), it is
        # what the pinning channel and the P2 addend both read, and a
        # second arrival term beside it is what round 1's split was.  Kept
        # logged so the substrate's own measurement stays visible beside
        # the plant's B (`edge_addend`) and the drive actually used
        # (`A_eff`).  n == 0 -> 0.0: nothing arrived, nothing accrued
        # unchecked.
        v_checked = sum(1 for v in tr.result.verdicts
                        if v.status.value == "VERIFIED")
        v_refuted = sum(1 for v in tr.result.verdicts
                        if v.status.value == "REFUTED")
        v_unchecked = sum(1 for v in tr.result.verdicts
                          if v.status.value == "UNCHECKABLE")
        n_offered = v_checked + v_refuted + v_unchecked
        st.backlog_rate = zoh_lag(
            st.backlog_rate,
            (v_unchecked / n_offered) if n_offered else 0.0,
            1.0 / st.p.tau_D, H_STEP)
        # THE BOUNDARY SCORING (the plan's Q4), AFTER the boundary turn's
        # CEN work so the charge sits in that turn's real per-turn spend
        # through the SAME C11 ledger (never a side ledger); DEFERRED when
        # the turn cannot afford it, EXPIRED as an observable, never debt.
        c_charged = 0
        if is_self_boundary:
            rep = st.score_commitments(turn)
            c_charged = 0 if rep is None else int(rep.charged)
        plant = st._plant_step(sch)
        st.log.append(Stage2LogRow(
            turn=turn, t=plant["t"], backlog=backlog_before,
            backlog_ema=st.backlog_ema,
            G=plant["G"], D=plant["D"], c=plant["c"],
            verdicts_V=v_checked, verdicts_R=v_refuted,
            verdicts_U=v_unchecked,
            rejected=len(tr.result.rejected_proposals),
            derivations=tr.result.derivations_total,
            cut_depth_max=tr.result.cut_depth_max,
            engine_rev=tr.txn_rev,
            routed=routed, backlog_rate=st.backlog_rate,
            A_eff=st.agent.traj.log[-1].A_eff,
            edge_addend=st.agent.traj.log[-1].edge_addend,
            coverage=st.coverage,
            open_commitments=st.open_commitments,
            expired=st.commitments_expired,
            commitment_derivations=c_charged,
            memory_epoch=st.memory_epoch(),
            vocation_adopted=bool(st.vocation is not None
                                  and st.vocation.adopted),
            vocation_directed=(0 if vrep is None else int(vrep.directed)),
            vocation_commitments=(0 if vrep is None else int(vrep.n)),
            vocation_directed_share=(None if vrep is None
                                     else vrep.share),
            talking_bytes=talking_bytes,
            talking_actions=talking_actions,
            talking_applied=talking_applied,
            talking_applied_ids=talking_applied_ids,
            talking_applied_classes=talking_applied_classes,
            talking_refused=talking_refused,
            encode_salience=st.encode_salience,
            encode_admitted=st.encode_admitted,
            encode_denied_total=st.encode_denied,
            inward_share=inward_share))
        st.turn = turn
        if checkpoint_fn is not None and not checkpoint_fn(turn, st):
            break
    return st
