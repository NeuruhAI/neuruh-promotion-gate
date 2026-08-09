# Neuruh Promotion Gate

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
