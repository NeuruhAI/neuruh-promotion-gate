from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from neuruh_promotion_gate import *
H=sha256_ref
policy=PromotionPolicy("promotion.synthetic",("policy",),("canary",),50,0,True,True,True)
req=PromotionRequest("req-synthetic","proposal-synthetic",H("proposal"),"policy-synthetic","policy","v1","v2",H("summary"),100,True,H("tests"),0,0,H("approval"),H("reversibility"),"canary","2026-08-09T20:01:00Z")
d=PromotionGate(policy).evaluate(req,decision_id="promotion-synthetic",decided_at="2026-08-09T20:02:00Z")
Path(__file__).with_name("promotion.synthetic.json").write_text(json.dumps(d.to_dict(),indent=2,sort_keys=True)+"\n")
print(d.promotion_digest)
