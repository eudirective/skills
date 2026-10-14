#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path
import source_text_ingest as sti
import source_text_gate as stg

PACK_VERSION="0.5.0"

def validate(pack: Path):
    manifest=json.loads((pack/"source_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("pack_version")!=PACK_VERSION or manifest.get("manifest_version")!=PACK_VERSION:
        raise ValueError("expected core source pack 0.5.0; historical baseline migration is no longer a normal finalization path")
    gate=stg.inspect(pack)
    if gate["status"]!="complete": raise ValueError(f"C1 representation gate blocked: {gate['blocked_source_count']}")
    if manifest.get("completion_status")!="c1_source_representation_complete": raise ValueError("completion status is not c1_source_representation_complete")
    if len(manifest.get("sources",[]))!=45: raise ValueError("expected 45 logical core sources")
    return {"status":"valid","pack_version":PACK_VERSION,"logical_source_count":45,"representation_count":sum(len(s.get("representations",[])) for s in manifest["sources"]),"completion_status":manifest["completion_status"]}

def finalize(input_pack: Path, output_pack: Path):
    validate(input_pack)
    if output_pack.exists(): shutil.rmtree(output_pack)
    shutil.copytree(input_pack,output_pack)
    manifest=json.loads((output_pack/"source_manifest.json").read_text(encoding="utf-8"))
    sti.update_ingestion_files(output_pack,manifest,manifest["live_verification_date"])
    sti.regenerate_checksums(output_pack)
    return validate(output_pack)

def main():
    ap=argparse.ArgumentParser(description="Validate or deterministically re-finalize the current core-only 0.5.0 source pack")
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("finalize"); p.add_argument("input_pack"); p.add_argument("output_pack")
    p=sub.add_parser("validate"); p.add_argument("pack")
    a=ap.parse_args()
    try:
        out=finalize(Path(a.input_pack),Path(a.output_pack)) if a.cmd=="finalize" else validate(Path(a.pack))
        print(json.dumps(out,sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"status":"invalid","error":str(exc)},sort_keys=True),file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
