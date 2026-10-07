# crop-steering-engine

The **pure, HA-independent crop-steering decision core**: a pure-Python package with no
runtime dependency, which runs identically in the f2-control add-on (the controller app) and
in its tests. The add-on carries a copy, `addons/f2_control/f2_control/crop_steering_engine/`,
which CI keeps identical to `src/`.

```python
from crop_steering_engine import decide, ZoneParams, ZoneSnapshot

phase, p2_threshold, fire, size_pct, reason = decide(snapshot, params)
```

`decide(s, p)` is a plain function over two dataclasses — no I/O, no Home Assistant,
deterministic. It implements the 4-phase (P0→P3) state machine, EC steering, the
anti-lockout high-EC flush (any phase), the P3 dryback hold and rescue, the lights-on
starvation watchdog, and the daily-volume budget cap. The IO shell (reading sensors,
driving valves, durable state, the 30-min notifier) lives in the host service, not here.

## Dev

```bash
pip install -e ".[dev]"
pytest          # offline unit tests, no hardware
ruff check .
```
