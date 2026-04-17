# pbg-tellurium

Process-bigraph wrapper for [Tellurium](https://tellurium.analogmachine.org/) /
[libroadrunner](https://libroadrunner.org/) SBML &amp; Antimony model
simulation. Exposes any SBML or Antimony model as a `process-bigraph`
`Process` that steps in lockstep with the rest of a composite, so you
can compose kinetic models alongside other simulators (metabolic flux,
spatial, agent-based) inside a single bigraph document.

## Installation

```bash
git clone <this-repo-url> pbg-tellurium
cd pbg-tellurium
uv venv .venv && source .venv/bin/activate
uv pip install -e .
uv pip install bigraph-viz matplotlib  # optional, for the demo report
```

## Quick Start

```python
from process_bigraph import Composite, allocate_core, gather_emitter_results
from process_bigraph.emitter import RAMEmitter
from pbg_tellurium import TelluriumProcess, make_tellurium_document

ANTIMONY = """
model decay
  S1 = 10; S2 = 0
  S1 -> S2; k*S1; k = 0.3
end
"""

core = allocate_core()
core.register_link('TelluriumProcess', TelluriumProcess)
core.register_link('ram-emitter', RAMEmitter)

doc = make_tellurium_document(model=ANTIMONY, interval=1.0)
sim = Composite({'state': doc}, core=core)
sim.run(10.0)

results = gather_emitter_results(sim)[('emitter',)]
print(results[-1]['species'])  # {'S1': 0.498..., 'S2': 9.502...}
```

## API Reference

### `TelluriumProcess` (Process)

Time-driven bridge wrapping a RoadRunner instance. The model is loaded
lazily on the first `update()` call; each subsequent update advances
the simulator by `interval` seconds (or whatever unit the model uses).

| Port      | Direction | Schema                   | Notes |
|-----------|-----------|--------------------------|-------|
| `species` | input     | `maybe[map[float]]`      | Optional override pushed into RR before stepping |
| `species` | output    | `overwrite[map[float]]`  | Floating-species concentrations |
| `rates`   | output    | `overwrite[map[float]]`  | Current reaction rates |
| `parameters` | output | `overwrite[map[float]]`  | Global parameter values |
| `time`    | output    | `overwrite[float]`       | Current simulator time |

Config (all optional except one of `model`/`model_file`):

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `model` | string | `''` | Antimony or SBML source |
| `model_format` | string | `'antimony'` | `'antimony'` or `'sbml'` |
| `model_file` | string | `''` | Path to `.ant`/`.txt`/`.xml` file (takes precedence) |
| `integrator` | string | `'cvode'` | `'cvode'` (deterministic) or `'gillespie'` (stochastic) |
| `absolute_tolerance` | float | `1e-10` | CVODE absolute tolerance |
| `relative_tolerance` | float | `1e-8`  | CVODE relative tolerance |
| `seed` | integer | `-1` | Stochastic RNG seed (`-1` = unset) |
| `species_overrides` | map[float] | `{}` | `{species_id: initial_value}` |
| `parameter_overrides` | map[float] | `{}` | `{parameter_id: value}` |
| `reset_on_init` | boolean | `true` | Call `rr.reset()` after overrides |

### `TelluriumStep` (Step)

One-shot simulation Step that returns a dense trajectory in a single
call. Use when you want a static time series rather than time-coupled
stepping with other processes.

Extra config: `start_time`, `end_time`, `n_points`.
Outputs: `time_series` (list[float]), `species_trajectories` (map[list]).

### `make_tellurium_document(...)`

Helper that produces a ready-to-run composite document wiring a
`TelluriumProcess` into a `stores` dict plus a RAM emitter.

## Architecture

`TelluriumProcess` follows the v2ecoli bridge pattern: RoadRunner owns
the internal ODE state, and the wrapper exposes it as typed PBG ports.

```
  +------------------------+
  | TelluriumProcess       |
  |                        |
  |  ┌──────────────────┐  |
  |  │ RoadRunner (C++) │──┼──► species : map[float]
  |  │ integrators,     │  |──► rates   : map[float]
  |  │ Antimony/SBML    │  |──► parameters : map[float]
  |  │                  │  |──► time    : float
  |  └──────────────────┘  |
  |           ▲            |
  |           │            |
  |       species (opt)    |
  +------------------------+
```

The input `species` port lets external processes push values back into
RoadRunner each step — useful for coupling a kinetic model to a
spatial / stochastic compartment simulator.

## Demo

```bash
python demo/demo_report.py
```

Runs three distinct simulations — Lotka-Volterra predator-prey,
repressilator gene oscillator, stochastic dimerization — and writes
`demo/report.html`, a self-contained report with Plotly time-series,
phase portraits, reaction-rate traces, colored bigraph-viz diagrams,
Antimony source listings, and interactive composite-document trees.
The report opens automatically in Safari.

## Testing

```bash
pytest tests/
```

All tests are offline: models are declared inline as Antimony
strings, so no network or external fixtures are required.
