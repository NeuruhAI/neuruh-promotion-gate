import unittest
from neuruh_promotion_gate import *
H=sha256_ref
def policy(**kw):
    d=dict(policy_id="pg",allowed_target_kinds=("policy",),allowed_stages=("canary","pilot"),min_sample_count=10,max_regressions=1,require_tests=True,require_human_approval=True,require_reversibility=True); d.update(kw); return PromotionPolicy(**d)
def req(**kw):
    d=dict(request_id="r1",proposal_id="p1",proposal_digest=H("proposal"),target_id="t1",target_kind="policy",current_version="v1",candidate_version="v2",calibration_summary_digest=H("summary"),sample_count=10,tests_passed=True,test_report_digest=H("tests"),regression_count=0,critical_regression_count=0,human_approval_digest=H("approval"),reversibility_contract_digest=H("rev"),requested_stage="canary",requested_at="2026-08-09T20:01:00Z"); d.update(kw); return PromotionRequest(**d)
def decide(r=None,p=None,**kw):
    return PromotionGate(p or policy()).evaluate(r or req(),decision_id=kw.get("decision_id","d1"),decided_at=kw.get("decided_at","2026-08-09T20:02:00Z"))
class Tests(unittest.TestCase):
    def bad(self,fn):
        with self.assertRaises(PromotionValidationError): fn()
    def test_policy_valid(self): policy().validate()
    def test_policy_version_deterministic(self): self.assertEqual(policy().version,policy().version)
    def test_policy_empty_kinds(self): self.bad(lambda:policy(allowed_target_kinds=()).validate())
    def test_policy_unknown_kind(self): self.bad(lambda:policy(allowed_target_kinds=("weights",)).validate())
    def test_policy_duplicate_kind(self): self.bad(lambda:policy(allowed_target_kinds=("policy","policy")).validate())
    def test_policy_empty_stages(self): self.bad(lambda:policy(allowed_stages=()).validate())
    def test_policy_unknown_stage(self): self.bad(lambda:policy(allowed_stages=("root",)).validate())
    def test_policy_duplicate_stage(self): self.bad(lambda:policy(allowed_stages=("canary","canary")).validate())
    def test_policy_zero_samples(self): self.bad(lambda:policy(min_sample_count=0).validate())
    def test_policy_bool_samples(self): self.bad(lambda:policy(min_sample_count=True).validate())
    def test_policy_negative_regressions(self): self.bad(lambda:policy(max_regressions=-1).validate())
    def test_policy_bool_flag(self): self.bad(lambda:policy(require_tests=1).validate())
    def test_request_valid(self): req().validate()
    def test_request_digest_deterministic(self): self.assertEqual(req().digest,req().digest)
    def test_request_unknown_kind(self): self.bad(lambda:req(target_kind="weights").validate())
    def test_request_same_version(self): self.bad(lambda:req(candidate_version="v1").validate())
    def test_request_zero_samples(self): self.bad(lambda:req(sample_count=0).validate())
    def test_request_bool_samples(self): self.bad(lambda:req(sample_count=True).validate())
    def test_tests_true_requires_report(self): self.bad(lambda:req(test_report_digest=None).validate())
    def test_tests_false_allows_no_report(self): req(tests_passed=False,test_report_digest=None).validate()
    def test_bad_proposal_digest(self): self.bad(lambda:req(proposal_digest="bad").validate())
    def test_bad_summary_digest(self): self.bad(lambda:req(calibration_summary_digest="bad").validate())
    def test_bad_approval_digest(self): self.bad(lambda:req(human_approval_digest="bad").validate())
    def test_bad_reversibility_digest(self): self.bad(lambda:req(reversibility_contract_digest="bad").validate())
    def test_negative_regressions(self): self.bad(lambda:req(regression_count=-1).validate())
    def test_critical_gt_total(self): self.bad(lambda:req(regression_count=0,critical_regression_count=1).validate())
    def test_unknown_stage(self): self.bad(lambda:req(requested_stage="root").validate())
    def test_bad_time(self): self.bad(lambda:req(requested_at="wat").validate())
    def test_promote(self): self.assertEqual(decide().decision,"promote")
    def test_promote_no_deployment_authority(self): self.assertFalse(decide().deployment_authority)
    def test_hold_missing_tests(self): self.assertEqual(decide(req(tests_passed=False,test_report_digest=None)).decision,"hold")
    def test_hold_low_samples(self): self.assertEqual(decide(req(sample_count=9)).decision,"hold")
    def test_hold_too_many_regressions(self): self.assertEqual(decide(req(regression_count=2)).decision,"hold")
    def test_hold_missing_approval(self): self.assertEqual(decide(req(human_approval_digest=None)).decision,"hold")
    def test_hold_missing_reversibility(self): self.assertEqual(decide(req(reversibility_contract_digest=None)).decision,"hold")
    def test_block_critical_regression(self): self.assertEqual(decide(req(regression_count=1,critical_regression_count=1)).decision,"block")
    def test_block_disallowed_target(self):
        p=policy(allowed_target_kinds=("prompt_config",)); self.assertEqual(decide(p=p).decision,"block")
    def test_block_disallowed_stage(self):
        p=policy(allowed_stages=("pilot",)); self.assertEqual(decide(p=p).decision,"block")
    def test_policy_can_disable_approval_requirement(self):
        p=policy(require_human_approval=False); self.assertEqual(decide(req(human_approval_digest=None),p).decision,"promote")
    def test_policy_can_disable_reversibility_requirement(self):
        p=policy(require_reversibility=False); self.assertEqual(decide(req(reversibility_contract_digest=None),p).decision,"promote")
    def test_policy_can_disable_test_requirement(self):
        p=policy(require_tests=False); self.assertEqual(decide(req(tests_passed=False,test_report_digest=None),p).decision,"promote")
    def test_decision_before_request(self): self.bad(lambda:decide(decided_at="2026-08-09T20:00:00Z"))
    def test_decision_roundtrip(self): self.assertEqual(PromotionDecision.from_mapping(decide().to_dict()),decide())
    def test_decision_bad_schema(self):
        x=decide().to_dict(); x["schema_version"]="x"; self.bad(lambda:PromotionDecision.from_mapping(x))
    def test_decision_unknown_field(self):
        x=decide().to_dict(); x["deploy"]=True; self.bad(lambda:PromotionDecision.from_mapping(x))
    def test_decision_authority_true_rejected(self):
        x=decide().to_dict(); x["deployment_authority"]=True; x["promotion_digest"]=H("wrong"); self.bad(lambda:PromotionDecision.from_mapping(x))
    def test_decision_tamper_digest(self):
        x=decide().to_dict(); x["decision"]="hold"; self.bad(lambda:PromotionDecision.from_mapping(x))
    def test_decision_reasons_nonempty(self):
        d=decide(); self.assertTrue(d.reasons)
    def test_promote_reason_explicit_eligibility(self):
        self.assertIn("lifecycle eligibility only",decide().reasons[0])
