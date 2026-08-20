# Neuruh Promotion Gate

[![ci](https://github.com/NeuruhAI/neuruh-promotion-gate/actions/workflows/ci.yml/badge.svg)](https://github.com/NeuruhAI/neuruh-promotion-gate/actions/workflows/ci.yml)

Public Commons Release 020. A deterministic, fail-closed lifecycle eligibility gate for candidate learning updates.

The gate evaluates a content-bound proposal against declared promotion prerequisites such as:
- allowed target kind and requested lifecycle stage;
- calibration sample count;
- passing test evidence;
- regression counts;
- human approval;
- reversibility contract.

It returns `PROMOTE`, `HOLD`, or `BLOCK`.

**Critical boundary:** `PROMOTE` means *eligible to progress to the requested lifecycle stage*. It is not deployment authority and this package cannot deploy or mutate anything.

## Install

```bash
git clone https://github.com/NeuruhAI/neuruh-promotion-gate.git
cd neuruh-promotion-gate
python -m venv .venv
source .venv/bin/activate
pip install .
```

Or install a pinned release directly:

```bash
pip install "neuruh-promotion-gate @ git+https://github.com/NeuruhAI/neuruh-promotion-gate.git@v0.1.1-alpha"
```

## Sixty-second example

The repository ships synthetic fixtures. Check one with the installed CLI:

```bash
neuruh-promotion-gate validate examples/promotion.synthetic.json
neuruh-promotion-gate digest examples/promotion.synthetic.json
```

Expected output:

```text
{"decision": "promote", "decision_id": "promotion-synthetic", "deployment_authority": false, "ok": true}
sha256:6e40e1a04d6884db194e2f40f1fdc3b2c3dcef5137092e7dc4de2b6154a4da2e
```

`inspect` prints the full parsed object as indented JSON.

`examples/build_synthetic.py` regenerates the fixtures from scratch, so the construction path can be read end to end.

Bad input is reported, never raised as a traceback: a missing file, unreadable JSON, or a rejected object prints `error: ...` on stderr and exits `2`.

## API

| Name | Notes |
| --- | --- |
| `DECISIONS` | Declared vocabulary. |
| `SCHEMA_VERSION` | Declared vocabulary. |
| `STAGES` | Declared vocabulary. |
| `TARGET_KINDS` | Declared vocabulary. |
| `PromotionDecision` | Fields: `decision_id`, `request_digest`, `policy_id`, `policy_version`, `decision`, `reasons`… |
| `PromotionGate` |  |
| `PromotionPolicy` | Fields: `policy_id`, `allowed_target_kinds`, `allowed_stages`, `min_sample_count`, `max_regressions`, `require_tests`… |
| `PromotionRequest` | Fields: `request_id`, `proposal_id`, `proposal_digest`, `target_id`, `target_kind`, `current_version`… |
| `PromotionValidationError` | Raised for every rejection. |
| `canonical_json(value)` |  |
| `sha256_ref(value)` |  |

The published schema is [`schema/promotion-decision.v0.1.schema.json`](schema/promotion-decision.v0.1.schema.json).

## Test

```bash
python -m unittest discover -s tests -v
```

## Safety boundary

This package validates, records, and reports. It holds no credentials, performs no network I/O,
and grants no authority. A valid object means the claims inside it are internally consistent and
content-bound — not that the underlying action was correct, permitted, or actually happened.
Digests and hash links are tamper evidence, not signatures: they detect modification, they do
not establish who wrote an entry.

Only synthetic fixtures ship here: no production data, endpoints, policies, or topology. See
[`ARCHITECTURE.md`](ARCHITECTURE.md), [`PUBLIC_PRIVATE_BOUNDARY.md`](PUBLIC_PRIVATE_BOUNDARY.md), [`SECURITY.md`](SECURITY.md), and the
[Neuruh Public Commons boundary](https://github.com/NeuruhAI/public-commons/blob/main/PUBLIC_PRIVATE_BOUNDARY.md).

## License

Apache License 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
