from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json, re
from typing import Any, Mapping, Sequence

SCHEMA_VERSION="neuruh.promotion-gate.v0.1"
TARGET_KINDS={"policy","model_config","prompt_config","routing_config","threshold_config","workflow_config"}
STAGES={"sandbox","canary","pilot","production"}
DECISIONS={"promote","hold","block"}
HEX64=re.compile(r"^[0-9a-f]{64}$")

class PromotionValidationError(ValueError):
    """Fail-closed refusal for malformed promotion requests, policy mismatch, or tampered decisions."""

def canonical_json(value:Any)->str:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)

def sha256_ref(value:str|bytes)->str:
    if isinstance(value,str): value=value.encode("utf-8")
    return "sha256:"+sha256(value).hexdigest()

def _nonempty(v:Any,name:str)->str:
    if not isinstance(v,str) or not v.strip(): raise PromotionValidationError(f"{name} must be a non-empty string")
    return v

def _sha(v:Any,name:str)->str:
    v=_nonempty(v,name)
    if not v.startswith("sha256:") or not HEX64.fullmatch(v[7:]): raise PromotionValidationError(f"{name} must be sha256:<64 lowercase hex>")
    return v

def _time(v:Any,name:str)->datetime:
    v=_nonempty(v,name)
    try:d=datetime.fromisoformat(v.replace("Z","+00:00"))
    except ValueError as exc: raise PromotionValidationError(f"{name} must be RFC3339/ISO-8601") from exc
    if d.tzinfo is None: raise PromotionValidationError(f"{name} must include a timezone")
    return d.astimezone(timezone.utc)

def _keys(raw:Mapping[str,Any],required:set[str],optional:set[str],context:str)->None:
    missing=sorted(required-set(raw)); unknown=sorted(set(raw)-required-optional)
    if missing: raise PromotionValidationError(f"{context} missing required field(s): {', '.join(missing)}")
    if unknown: raise PromotionValidationError(f"{context} contains unknown field(s): {', '.join(unknown)}")

def _strings(vals:Any,name:str,*,allow_empty:bool=False)->tuple[str,...]:
    if not isinstance(vals,list): raise PromotionValidationError(f"{name} must be an array")
    out=tuple(_nonempty(v,f"{name} item") for v in vals)
    if not allow_empty and not out: raise PromotionValidationError(f"{name} must not be empty")
    if len(out)!=len(set(out)): raise PromotionValidationError(f"{name} must not contain duplicates")
    return out

@dataclass(frozen=True)
class PromotionPolicy:
    policy_id:str
    allowed_target_kinds:tuple[str,...]
    allowed_stages:tuple[str,...]
    min_sample_count:int
    max_regressions:int
    require_tests:bool=True
    require_human_approval:bool=True
    require_reversibility:bool=True

    def canonical_dict(self)->dict[str,Any]:
        self.validate()
        return {"policy_id":self.policy_id,"allowed_target_kinds":list(self.allowed_target_kinds),"allowed_stages":list(self.allowed_stages),"min_sample_count":self.min_sample_count,"max_regressions":self.max_regressions,"require_tests":self.require_tests,"require_human_approval":self.require_human_approval,"require_reversibility":self.require_reversibility}

    @property
    def version(self)->str: return sha256_ref(canonical_json(self.canonical_dict()))

    def validate(self)->None:
        _nonempty(self.policy_id,"policy_id")
        if not self.allowed_target_kinds: raise PromotionValidationError("allowed_target_kinds must not be empty")
        if not set(self.allowed_target_kinds).issubset(TARGET_KINDS): raise PromotionValidationError("unknown allowed target kind")
        if len(self.allowed_target_kinds)!=len(set(self.allowed_target_kinds)): raise PromotionValidationError("allowed_target_kinds must be unique")
        if not self.allowed_stages: raise PromotionValidationError("allowed_stages must not be empty")
        if not set(self.allowed_stages).issubset(STAGES): raise PromotionValidationError("unknown allowed stage")
        if len(self.allowed_stages)!=len(set(self.allowed_stages)): raise PromotionValidationError("allowed_stages must be unique")
        if isinstance(self.min_sample_count,bool) or not isinstance(self.min_sample_count,int) or self.min_sample_count<1: raise PromotionValidationError("min_sample_count must be a positive integer")
        if isinstance(self.max_regressions,bool) or not isinstance(self.max_regressions,int) or self.max_regressions<0: raise PromotionValidationError("max_regressions must be a non-negative integer")
        for v,n in [(self.require_tests,"require_tests"),(self.require_human_approval,"require_human_approval"),(self.require_reversibility,"require_reversibility")]:
            if not isinstance(v,bool): raise PromotionValidationError(f"{n} must be boolean")

@dataclass(frozen=True)
class PromotionRequest:
    request_id:str
    proposal_id:str
    proposal_digest:str
    target_id:str
    target_kind:str
    current_version:str
    candidate_version:str
    calibration_summary_digest:str
    sample_count:int
    tests_passed:bool
    test_report_digest:str|None
    regression_count:int
    critical_regression_count:int
    human_approval_digest:str|None
    reversibility_contract_digest:str|None
    requested_stage:str
    requested_at:str

    def body_dict(self)->dict[str,Any]:
        self.validate()
        return {
            "request_id":self.request_id,"proposal_id":self.proposal_id,"proposal_digest":self.proposal_digest,"target_id":self.target_id,
            "target_kind":self.target_kind,"current_version":self.current_version,"candidate_version":self.candidate_version,
            "calibration_summary_digest":self.calibration_summary_digest,"sample_count":self.sample_count,"tests_passed":self.tests_passed,
            "test_report_digest":self.test_report_digest,"regression_count":self.regression_count,"critical_regression_count":self.critical_regression_count,
            "human_approval_digest":self.human_approval_digest,"reversibility_contract_digest":self.reversibility_contract_digest,
            "requested_stage":self.requested_stage,"requested_at":self.requested_at,
        }

    @property
    def digest(self)->str: return sha256_ref(canonical_json(self.body_dict()))

    def validate(self)->None:
        for v,n in [(self.request_id,"request_id"),(self.proposal_id,"proposal_id"),(self.target_id,"target_id"),(self.current_version,"current_version"),(self.candidate_version,"candidate_version")]: _nonempty(v,n)
        _sha(self.proposal_digest,"proposal_digest"); _sha(self.calibration_summary_digest,"calibration_summary_digest")
        if self.target_kind not in TARGET_KINDS: raise PromotionValidationError(f"unknown target_kind: {self.target_kind}")
        if self.current_version==self.candidate_version: raise PromotionValidationError("candidate_version must differ from current_version")
        if isinstance(self.sample_count,bool) or not isinstance(self.sample_count,int) or self.sample_count<1: raise PromotionValidationError("sample_count must be positive integer")
        if not isinstance(self.tests_passed,bool): raise PromotionValidationError("tests_passed must be boolean")
        if self.test_report_digest is not None: _sha(self.test_report_digest,"test_report_digest")
        if self.tests_passed and self.test_report_digest is None: raise PromotionValidationError("tests_passed requires test_report_digest")
        for v,n in [(self.regression_count,"regression_count"),(self.critical_regression_count,"critical_regression_count")]:
            if isinstance(v,bool) or not isinstance(v,int) or v<0: raise PromotionValidationError(f"{n} must be non-negative integer")
        if self.critical_regression_count>self.regression_count: raise PromotionValidationError("critical_regression_count cannot exceed regression_count")
        if self.human_approval_digest is not None: _sha(self.human_approval_digest,"human_approval_digest")
        if self.reversibility_contract_digest is not None: _sha(self.reversibility_contract_digest,"reversibility_contract_digest")
        if self.requested_stage not in STAGES: raise PromotionValidationError(f"unknown requested_stage: {self.requested_stage}")
        _time(self.requested_at,"requested_at")

@dataclass(frozen=True)
class PromotionDecision:
    decision_id:str
    request_digest:str
    policy_id:str
    policy_version:str
    decision:str
    reasons:tuple[str,...]
    decided_at:str
    deployment_authority:bool=False
    promotion_digest:str|None=None

    def body_dict(self)->dict[str,Any]:
        return {"schema_version":SCHEMA_VERSION,"decision_id":self.decision_id,"request_digest":self.request_digest,"policy_id":self.policy_id,"policy_version":self.policy_version,"decision":self.decision,"reasons":list(self.reasons),"decided_at":self.decided_at,"deployment_authority":self.deployment_authority}

    def calculated_digest(self)->str: return sha256_ref(canonical_json(self.body_dict()))

    def validate(self,*,check_digest:bool=True)->None:
        _nonempty(self.decision_id,"decision_id"); _sha(self.request_digest,"request_digest"); _nonempty(self.policy_id,"policy_id"); _sha(self.policy_version,"policy_version")
        if self.decision not in DECISIONS: raise PromotionValidationError(f"unknown promotion decision: {self.decision}")
        if not self.reasons: raise PromotionValidationError("reasons must not be empty")
        for r in self.reasons: _nonempty(r,"reason")
        if len(self.reasons)!=len(set(self.reasons)): raise PromotionValidationError("reasons must be unique")
        _time(self.decided_at,"decided_at")
        if self.deployment_authority is not False: raise PromotionValidationError("promotion decisions never grant deployment authority")
        if check_digest:
            if self.promotion_digest is None: raise PromotionValidationError("promotion_digest is required")
            _sha(self.promotion_digest,"promotion_digest")
            if self.promotion_digest!=self.calculated_digest(): raise PromotionValidationError("promotion_digest mismatch")

    def seal(self)->"PromotionDecision":
        self.validate(check_digest=False)
        obj=PromotionDecision(**{**self.__dict__,"promotion_digest":self.calculated_digest()}); obj.validate(); return obj

    def to_dict(self)->dict[str,Any]:
        self.validate(); out=self.body_dict(); out["promotion_digest"]=self.promotion_digest; return out

    @classmethod
    def from_mapping(cls,raw:Mapping[str,Any])->"PromotionDecision":
        req={"schema_version","decision_id","request_digest","policy_id","policy_version","decision","reasons","decided_at","deployment_authority","promotion_digest"}
        _keys(raw,req,set(),"promotion decision")
        if raw["schema_version"]!=SCHEMA_VERSION: raise PromotionValidationError("unsupported schema_version")
        obj=cls(decision_id=_nonempty(raw["decision_id"],"decision_id"),request_digest=_sha(raw["request_digest"],"request_digest"),policy_id=_nonempty(raw["policy_id"],"policy_id"),policy_version=_sha(raw["policy_version"],"policy_version"),decision=raw["decision"],reasons=_strings(raw["reasons"],"reasons"),decided_at=_nonempty(raw["decided_at"],"decided_at"),deployment_authority=raw["deployment_authority"],promotion_digest=_sha(raw["promotion_digest"],"promotion_digest"))
        obj.validate(); return obj

class PromotionGate:
    """Deterministic lifecycle eligibility gate. It never deploys, mutates, or grants deployment authority."""
    def __init__(self,policy:PromotionPolicy):
        policy.validate(); self.policy=policy

    def evaluate(self,request:PromotionRequest,*,decision_id:str,decided_at:str)->PromotionDecision:
        request.validate(); _nonempty(decision_id,"decision_id"); _time(decided_at,"decided_at")
        req_time=_time(request.requested_at,"requested_at"); dec_time=_time(decided_at,"decided_at")
        if dec_time<req_time: raise PromotionValidationError("decided_at cannot precede requested_at")
        reasons=[]
        # Structural/safety violations are BLOCK.
        if request.target_kind not in self.policy.allowed_target_kinds: reasons.append(f"target kind not allowed: {request.target_kind}")
        if request.requested_stage not in self.policy.allowed_stages: reasons.append(f"stage not allowed: {request.requested_stage}")
        if request.critical_regression_count>0: reasons.append(f"critical regressions present: {request.critical_regression_count}")
        if reasons:
            decision="block"
        else:
            # Missing evidence/prerequisites are HOLD.
            if self.policy.require_tests and not request.tests_passed: reasons.append("required tests did not pass")
            if self.policy.require_tests and request.test_report_digest is None: reasons.append("required test report missing")
            if request.sample_count<self.policy.min_sample_count: reasons.append(f"sample count {request.sample_count} below minimum {self.policy.min_sample_count}")
            if request.regression_count>self.policy.max_regressions: reasons.append(f"regressions {request.regression_count} exceed maximum {self.policy.max_regressions}")
            if self.policy.require_human_approval and request.human_approval_digest is None: reasons.append("required human approval missing")
            if self.policy.require_reversibility and request.reversibility_contract_digest is None: reasons.append("required reversibility contract missing")
            decision="hold" if reasons else "promote"
            if decision=="promote": reasons=["all declared promotion prerequisites satisfied; lifecycle eligibility only"]
        return PromotionDecision(decision_id,request.digest,self.policy.policy_id,self.policy.version,decision,tuple(reasons),decided_at,False).seal()
