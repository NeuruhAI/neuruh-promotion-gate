from __future__ import annotations
import argparse,json
from pathlib import Path
from .core import PromotionDecision
def main(argv=None):
    p=argparse.ArgumentParser(prog="neuruh-promotion-gate")
    sp=p.add_subparsers(dest="cmd",required=True)
    for n in ("validate","digest","inspect"):
        x=sp.add_parser(n); x.add_argument("file")
    a=p.parse_args(argv); obj=PromotionDecision.from_mapping(json.loads(Path(a.file).read_text()))
    if a.cmd=="validate": print(json.dumps({"ok":True,"decision_id":obj.decision_id,"decision":obj.decision,"deployment_authority":obj.deployment_authority},sort_keys=True))
    elif a.cmd=="digest": print(obj.promotion_digest)
    else: print(json.dumps(obj.to_dict(),indent=2,sort_keys=True))
if __name__=="__main__": main()
