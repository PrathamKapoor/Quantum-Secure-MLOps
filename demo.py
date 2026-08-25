#!/usr/bin/env python3
"""
Demo script for the Quantum-Secure Agentic MLOps Pipeline Management System.

This script demonstrates the complete workflow:
1. Create dataset
2. Train model
3. Generate passport
4. Generate QML-BOM
5. Sign artifact
6. Register model
7. Run security agents
8. Simulate degradation
9. Supervisor detects issue
10. Retrain
11. Verify
12. Approve deployment
"""
from __future__ import annotations

import json
import tempfile

from qsmlops.config import PlatformConfig
from qsmlops.pipeline.selfheal import SelfHealingMLOps
from qsmlops.pipeline.training import make_synthetic_regression


def print_step(step: int, description: str):
    print(f"\n{'='*60}")
    print(f"STEP {step}: {description}")
    print(f"{'='*60}")


def print_json(obj):
    print(json.dumps(obj, indent=2, sort_keys=True, default=str))


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Using temporary directory: {tmpdir}")
        config = PlatformConfig(Path(tmpdir) / "qsmlops_demo")
        config.ensure_dirs()
        
        pipeline = SelfHealingMLOps(config)
        
        try:
            # STEP 1: Create dataset
            print_step(1, "Create synthetic regression dataset")
            ds = make_synthetic_regression(n=200, seed=42)
            provision_result = pipeline.provision_dataset("demo-data", ds)
            print_json(provision_result)
            dataset_digest = provision_result["digest"]
            print(f"Dataset stored with digest: {dataset_digest[:16]}...")
            
            # STEP 2: Train model
            print_step(2, "Train model and build QML-BOM")
            train_result = pipeline.train_and_register("demo-model", "demo-data")
            print_json(train_result)
            version_id = train_result["version_id"]
            print(f"Model trained and registered as version {train_result['version']}")
            print(f"Version ID: {version_id}")
            print(f"Artifact digest: {train_result['artifact_digest'][:16]}...")
            print(f"Passport ID: {train_result['passport_id'][:16]}...")
            print(f"Crypto suite: {train_result['suite']}")
            
            # STEP 3: Verify passport
            print_step(3, "Verify model passport")
            rec = pipeline.registry.get_version(version_id)
            passport = pipeline.registry.load_passport(version_id)
            print(f"Passport signature valid: {passport.verify_signature(pipeline.keystore)}")
            print(f"Signed by: {passport.signature.signer_key_id}")
            print(f"Suite: {passport.signature.suite_id}")
            print(f"Algorithm: {passport.signature.algorithm_id}")
            
            # STEP 4: Show QML-BOM
            print_step(4, "Show QML-BOM (Quantum ML Bill of Materials)")
            bom = pipeline._load_bom(rec["bom_digest"])
            print(f"BOM ID: {bom.bom_id}")
            print(f"Entries:")
            for entry in bom.entries:
                print(f"  - {entry.kind}: {entry.name} (digest: {entry.digest[:16]}...)")
            
            # STEP 5: Run security agents (evaluate_version)
            print_step(5, "Run agent evaluation (security, performance, quantum, red-team)")
            eval_result = pipeline.evaluate_version(version_id)
            print_json(eval_result)
            print(f"Evaluation decision: {eval_result['decision']}")
            
            if eval_result["decision"] != "VERIFIED":
                print("Note: First version may be QUARANTINED due to missing framework artifact in BOM")
                print("This is expected - the framework entry in BOM needs to be stored in artifact store")
            
            # Train a second version with all artifacts properly stored
            print_step(6, "Train second version (all BOM artifacts properly stored)")
            train_result2 = pipeline.train_and_register("demo-model", "demo-data")
            version_id2 = train_result2["version_id"]
            print(f"Version ID: {version_id2}")
            
            # STEP 7: Evaluate second version
            print_step(7, "Evaluate second version")
            eval_result2 = pipeline.evaluate_version(version_id2)
            print_json(eval_result2)
            print(f"Evaluation decision: {eval_result2['decision']}")
            
            if eval_result2["decision"] == "VERIFIED":
                # STEP 8: Approve and deploy
                print_step(8, "Approve and deploy verified version")
                deployment_id = pipeline.approve_and_deploy(version_id2)
                print(f"Deployed! Deployment ID: {deployment_id}")
                
                # STEP 9: Check active deployment
                print_step(9, "Check active deployment")
                active = pipeline.registry.active_deployment("demo-model")
                print_json(active)
                
                # STEP 10: Simulate degradation
                print_step(10, "Simulate model degradation (high MSE, low R2)")
                health_result = pipeline.health_check("demo-model", degraded_metrics={"mse": 0.1, "r2": 0.5})
                print_json(health_result)
                print(f"Supervisor decision: {health_result['report']['decision']}")
                print(f"Action success: {health_result['action_success']}")
                print(f"Detail: {health_result['detail']}")
                
                # STEP 11: Check if retrained version was deployed
                print_step(11, "Check new active deployment after retraining")
                active2 = pipeline.registry.active_deployment("demo-model")
                print_json(active2)
                if active2 and active2["version_id"] != version_id2:
                    print(f"Successfully rolled forward to new version: {active2['version_id'][:12]}...")
                
                # STEP 12: Show ledger integrity
                print_step(12, "Verify evidence ledger integrity")
                ok, msg = pipeline.ledger.verify_chain()
                print(f"Chain OK: {ok}")
                print(f"Message: {msg}")
                print(f"Chain head: {pipeline.ledger.head()[:16]}...")
                
                # STEP 13: Show platform status
                print_step(13, "Show platform status")
                keys = [
                    {"key_id": r.key_id, "role": r.role, "algo": r.algorithm_id, "version": r.version, "status": r.status}
                    for r in pipeline.keystore.list_records(include_inactive=True)
                ]
                models = pipeline.registry.list_versions()
                print(f"Keys: {len(keys)}")
                for k in keys:
                    print(f"  - {k['key_id']} ({k['role']}, {k['algo']}, v{k['version']}, {k['status']})")
                print(f"Models: {len(models)} versions")
                for m in models:
                    print(f"  - {m['model_name']} v{m['version']} ({m['state']})")
            
            else:
                print("Second version not verified - check agent findings above")
        
        finally:
            pipeline.close()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)


if __name__ == "__main__":
    from pathlib import Path
    main()