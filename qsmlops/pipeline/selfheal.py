"""Self-healing MLOps lifecycle orchestrator.

Wires every platform component into one autonomous loop:

    provision data -> train -> build QML-BOM -> sign passport -> register
    -> agent evaluation -> supervisor decision -> deploy gate
    -> health monitoring -> automatic recovery (retrain / rollback / quarantine)

Recovery policy: a failing deployed model triggers RETRAIN (new version,
fresh verification); if retrained versions keep failing, the supervisor's
learning store escalates and the previous good version is rolled back.
"""
from __future__ import annotations

import json
import platform
import time
from pathlib import Path

from qsmlops.agents.data_agent import DataAgent
from qsmlops.agents.performance_agent import PerformanceAgent
from qsmlops.agents.quantum_agent import QuantumSecurityAgent
from qsmlops.agents.redteam import RedTeamAgent
from qsmlops.agents.security_agent import SecurityAgent
from qsmlops.artifacts.store import ArtifactStore
from qsmlops.config import PlatformConfig
from qsmlops.crypto.agility import AgilityEngine
from qsmlops.crypto.hashing import HASH_ALGORITHM, canonical_json, sha3_hex
from qsmlops.crypto.keys import KeyStore
from qsmlops.evidence.ledger import EvidenceLedger
from qsmlops.pipeline.training import (
    Dataset,
    deserialize_model,
    evaluate_linear,
    make_synthetic_regression,
    serialize_model,
    train_linear_regression,
)
from qsmlops.passport.passport import new_passport
from qsmlops.registry.registry import ModelRegistry
from qsmlops.supervisor.decisions import Decision
from qsmlops.supervisor.learning import LearningStore
from qsmlops.supervisor.supervisor import AdaptiveSupervisor
from qsmlops.supplychain.bom import QMLBOM

PRODUCER = "producer"
VERIFIER = "verifier"


class SelfHealingMLOps:
    def __init__(self, config: PlatformConfig | None = None) -> None:
        self.config = config or PlatformConfig()
        self.config.ensure_dirs()
        self.artifacts = ArtifactStore(self.config.artifacts_dir)
        self.keystore = KeyStore(self.config.keys_dir)
        self.ledger = EvidenceLedger(self.config.ledger_path)
        self.registry = ModelRegistry(
            self.config.registry_path, self.artifacts, self.keystore, self.ledger
        )
        self.agility = AgilityEngine()
        self._provision_keys()

        self.dataset_cache: dict[str, Dataset] = {}
        self.train_fn_cache: dict[str, object] = {}
        self.last_observations: dict[str, list[dict]] = {}   # model -> latest agent sweep (dicts)
        self.last_drift_status: dict[str, dict] = {}         # model -> latest drift summary

        self.agents = [
            DataAgent(self.artifacts),
            PerformanceAgent(),
            SecurityAgent(self.artifacts),
            QuantumSecurityAgent(self.agility),
            RedTeamAgent(self.artifacts),
        ]
        self.learner = LearningStore(
            self.config.learning_path, max_consecutive_failures=2
        )
        self.supervisor = AdaptiveSupervisor(
            agents=self.agents,
            registry=self.registry,
            keystore=self.keystore,
            agility=self.agility,
            ledger=self.ledger,
            artifacts=self.artifacts,
            learner=self.learner,
            verifier_owner=VERIFIER,
        )
        self.supervisor.set_retrain_function(self._auto_retrain)

    # ---------- bootstrap ----------
    def _provision_keys(self) -> None:
        owners = {r.owner for r in self.keystore.list_records(role="SIGNER")}
        for owner in (PRODUCER, VERIFIER):
            if owner not in owners:
                suite = self.agility.select_suite()
                self.keystore.generate_keypair("SIGNER", suite.signature_algorithm, owner=owner)

    def _dataset_index_path(self) -> Path:
        """Path to the dataset index file (outside content-addressed store)."""
        return self.config.root / "datasets_index.json"

    def _load_dataset_index(self) -> dict:
        """Load the dataset name -> digest mapping."""
        path = self._dataset_index_path()
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_dataset_index(self, index: dict) -> None:
        """Save the dataset name -> digest mapping."""
        path = self._dataset_index_path()
        path.write_text(json.dumps(index, sort_keys=True), encoding="utf-8")

    def _load_dataset(self, name: str) -> Dataset | None:
        """Load a dataset from the artifact store by name."""
        index = self._load_dataset_index()
        digest = index.get(name)
        if digest is None:
            return None
        doc = self.artifacts.get_if_exists(digest)
        if doc is None:
            return None
        data = json.loads(doc.decode("utf-8"))
        return Dataset(samples=data["samples"], feature_names=data["feature_names"])

    # ---------- lifecycle ----------
    def provision_dataset(self, name: str, dataset: Dataset) -> dict:
        payload = json.dumps({"samples": dataset.samples, "feature_names": dataset.feature_names}).encode("utf-8")
        digest = self.artifacts.put(payload)
        # Update dataset index
        index = self._load_dataset_index()
        index[name] = digest
        self._save_dataset_index(index)
        bom = QMLBOM.create()
        bom.add_entry("dataset", name, digest, origin="internal-synthetic")
        self.dataset_cache[name] = dataset
        self.ledger.append(
            {"type": "dataset_provisioned", "name": name, "digest": digest}
        )
        return {"bom": bom, "digest": digest}

    def train_and_register(
        self,
        model_name: str,
        dataset_name: str,
        version: int | None = None,
        dataset: Dataset | None = None,
        framework: str = "reference",
        hyperparameters: dict | None = None,
    ) -> dict:
        """Train, build QML-BOM, sign passport and register a model version.

        framework="reference" keeps the pure-Python linear trainer (default,
        byte-reproducible). framework="sklearn" trains a real scikit-learn
        model through the Phase-2 adapter layer; pytorch/tensorflow follow the
        same interface when those frameworks are installed.
        """
        ds = dataset or self.dataset_cache.get(dataset_name) or self._load_dataset(dataset_name)
        if ds is None:
            raise ValueError(f"unknown dataset {dataset_name!r}; call provision_dataset first")
        if framework == "reference":
            t0 = time.time()
            model = train_linear_regression(ds)
            metrics = evaluate_linear(model, ds)
            artifact_bytes = serialize_model(model)
            training_info = {"algorithm": "linear-regression-gd", "epochs": 300,
                             "dataset": dataset_name, "n_samples": len(ds.samples),
                             "framework": "reference",
                             "hyperparameters": {"epochs": 300, "lr": 0.02, "seed": 7},
                             "training_duration_ms": round((time.time() - t0) * 1000, 2)}
        else:
            from qsmlops.ml.adapters import get_trainer, get_serializer

            hyperparameters = dict(hyperparameters or {})
            if framework in ("sklearn", "scikit-learn") and "estimator_class" not in hyperparameters:
                from sklearn.linear_model import LinearRegression

                hyperparameters.setdefault("estimator_class", LinearRegression)
            trainer = get_trainer(framework, **hyperparameters)
            import numpy as np

            X = np.asarray(ds.X, dtype=float)
            y = np.asarray(ds.y, dtype=float)
            split = max(1, int(0.8 * len(X)))
            t0 = time.time()
            result = trainer.train(X[:split], y[:split], X[split:], y[split:])
            training_duration_ms = round((time.time() - t0) * 1000, 2)
            model = result.model
            metrics = dict(result.metrics or {})
            preds = trainer.evaluate(model, X, y)
            if "mse" in preds and "r2" not in metrics:
                metrics.setdefault("mse", float(preds["mse"]))
            if "r2" in preds:
                metrics.setdefault("r2", float(preds["r2"]))
            artifact_bytes = get_serializer(framework).serialize(model)
            training_info = {"algorithm": f"{framework}:{result.metadata.model_type}",
                             "dataset": dataset_name, "n_samples": len(ds.samples),
                             "framework": framework,
                             "hyperparameters": result.metadata.hyperparameters,
                             "training_duration_ms": training_duration_ms}
        artifact_digest = sha3_hex(artifact_bytes)

        # Get the dataset digest from the index (consistent with provision_dataset)
        dataset_index = self._load_dataset_index()
        dataset_digest = dataset_index.get(dataset_name)
        if dataset_digest is None:
            # Fallback: compute from samples (for backward compat)
            data_payload = json.dumps(ds.samples).encode("utf-8")
            dataset_digest = sha3_hex(data_payload)

        bom = QMLBOM.create()
        bom.add_entry("dataset", dataset_name, dataset_digest, origin="internal-synthetic")
        if framework == "reference":
            code_digest = sha3_hex(serialize_model(model))
            framework_content = b"pure-python-gradient-descent"
            framework_name = "qsmlops-reference-trainer"
        else:
            code_digest = artifact_digest  # the serialized model bytes ARE the trained program
            framework_content = f"qsmlops-ml-adapter:{framework}".encode("utf-8")
            framework_name = f"qsmlops-adapter-{framework}"
        bom.add_entry("code", f"{model_name}-trainer", code_digest, version="1.0.0")
        bom.add_entry("artifact", model_name, artifact_digest, metadata={"metrics": metrics})
        framework_digest = sha3_hex(framework_content)
        self.artifacts.put(framework_content)
        bom.add_entry(
            "framework",
            framework_name,
            framework_digest,
            version="1.0.0",
        )

        # Phase 4 lineage components: a fingerprint of the runtime environment
        # the model was produced in, plus the third-party trainer dependencies
        # actually in use. Entry bytes live in the artifact store so agents can
        # re-verify every declared digest.
        env_doc = {
            "python_version": platform.python_version(),
            "platform": platform.platform(terse=True),
            "hardware": "cpu",
        }
        env_digest = self.artifacts.put(canonical_json(env_doc))
        bom.add_entry(
            "hardware",
            f"{model_name}-environment",
            env_digest,
            version="1.0.0",
            metadata={"python": env_doc["python_version"]},
        )
        dep_package = {"sklearn": "scikit-learn", "scikit-learn": "scikit-learn"}.get(
            str(framework).lower()
        )
        if dep_package:
            import importlib.metadata as importlib_metadata

            try:
                dep_version = importlib_metadata.version(dep_package)
            except importlib_metadata.PackageNotFoundError:
                dep_version = None
            if dep_version:
                dep_digest = self.artifacts.put(
                    canonical_json({"package": dep_package, "version": dep_version})
                )
                bom.add_entry(
                    "dependency", dep_package, dep_digest, version=dep_version, origin="pypi"
                )

        if version is None:
            existing = [v["version"] for v in self.registry.list_versions(model_name)]
            version = (max(existing) + 1) if existing else 1

        signing_suite = self.agility.select_suite()
        passport = new_passport(
            name=model_name,
            version=version,
            owner=PRODUCER,
            bom_digest=bom.digest(),
            artifact_digest=artifact_digest,
            training_info=training_info,
            metrics=metrics,
            environment={
                "python": platform.python_version(),
                "framework": "reference" if framework == "reference" else framework,
                "hardware": "cpu",
            },
            dataset_provenance={
                "bom_digest": bom.digest(),
                "dataset_name": dataset_name,
                "dataset_digest": dataset_digest,
                "n_samples": len(ds.samples),
                "feature_names": list(ds.feature_names),
                "origin": "internal-synthetic",
            },
            security_status={
                "state": "PENDING_REVIEW",
                "hash_algorithm": HASH_ALGORITHM,
                "suite_id": signing_suite.suite_id,
                "signature_algorithm": signing_suite.signature_algorithm,
                "artifact_digest": artifact_digest,
            },
        )
        passport.sign(self.keystore, self.agility, signer_owner=PRODUCER)
        version_id = self.registry.register(passport, artifact_bytes, bom.digest())

        bom_doc = bom.to_dict()
        self.artifacts.put(canonical_json(bom_doc))
        self.train_fn_cache[model_name] = _make_train_fn(train_linear_regression)
        return {
            "version_id": version_id,
            "version": version,
            "metrics": metrics,
            "artifact_digest": artifact_digest,
            "passport_id": passport.passport_id,
            "suite": passport.signature.suite_id,
        }

    def evaluate_version(self, version_id: str) -> dict:
        rec = self.registry.get_version(version_id)
        passport = self.registry.load_passport(version_id)
        context = {
            "subject_id": version_id,
            "passport": passport,
            "keystore": self.keystore,
            "bom": self._load_bom(rec["bom_digest"]),
            "artifact_digest": rec["artifact_digest"],
            "metrics": passport.metrics,
            "probe_inputs": [[0.1, -0.2], [0.5, 0.3], [-0.4, 0.6], [1.0, -1.0], [0.0, 0.0]],
        }
        checks: list[tuple[str, bool]] = []
        obs_objects = []
        for agent in self.agents:
            obs = agent.observe(context)
            obs_objects.append(obs)
            for f in obs.findings:
                if f.severity in ("CRITICAL", "HIGH"):
                    checks.append((f"{agent.name}:{f.name}", f.passed))
        packet = self.registry.verify_version(version_id, VERIFIER, checks)
        # Phase 5: evidence-based trust evaluation over the same sweep;
        # persisted by the registry and audited in the ledger.
        trust = self.registry.trust_evaluation(
            version_id, observations=obs_objects, actor=f"verify:{VERIFIER}"
        )
        return {
            "packet_id": packet.packet_id,
            "decision": packet.decision,
            "observations": [o.to_dict() for o in obs_objects],
            "trust": trust.to_dict(),
        }

    # ---------------- Phase 5: governed approval ----------------
    def request_approval(self, version_id: str, approver: str) -> dict:
        """Run verification + trust evaluation, then promote to APPROVED.

        The approval never deploys. Denials raise RuntimeError carrying the
        explainable trust report; every denial is audited by the registry.
        """
        evaluation = self.evaluate_version(version_id)
        if evaluation["decision"] != "VERIFIED":
            raise RuntimeError(f"verification refused approval: {evaluation['decision']}")
        trust = evaluation["trust"]
        if trust["decision"] not in ("TRUSTED", "CONDITIONALLY_TRUSTED"):
            raise RuntimeError(
                f"approval refused by trust gate: {trust['explanation']}"
            )
        from qsmlops.evidence.packet import SecurityCheck, VerificationPacket

        gate_packet = VerificationPacket.create(
            objective="deployment approval",
            actor=approver,
            inputs={
                "evaluation_packet": evaluation["packet_id"],
                "trust_score": trust["trust_score"],
                "trust_decision": trust["decision"],
            },
            security_checks=[
                SecurityCheck(name="trust_gate_passed", passed=True, severity="CRITICAL")
            ],
            decision="ACCEPT",
            status="CLOSED",
        )
        approval = self.registry.approve_deployment(version_id, approver, gate_packet)
        approval.update(
            {
                "verification_decision": evaluation["decision"],
                "blocking_conditions": trust["blocking_conditions"],
                "explanation": trust["explanation"],
            }
        )
        return approval

    def approve_and_deploy(self, version_id: str) -> str:
        result = self.evaluate_version(version_id)
        if result["decision"] != "VERIFIED":
            raise RuntimeError(f"verification refused deployment: {result['decision']}")
        if result["trust"]["decision"] not in ("TRUSTED", "CONDITIONALLY_TRUSTED"):
            raise RuntimeError(
                f"approval refused by trust gate: {result['trust']['explanation']}"
            )
        from qsmlops.evidence.packet import SecurityCheck, VerificationPacket

        gate_packet = VerificationPacket.create(
            objective="deployment approval",
            actor="supervisor",
            inputs={
                "evaluation_packet": result["packet_id"],
                "trust_score": result["trust"]["trust_score"],
                "trust_decision": result["trust"]["decision"],
            },
            security_checks=[SecurityCheck(name="verification_passed", passed=True, severity="CRITICAL")],
            decision="ACCEPT",
            status="CLOSED",
        )
        self.registry.approve_deployment(version_id, "supervisor", gate_packet)
        return self.registry.deploy(version_id, "supervisor")

    def health_check(self, model_name: str, degraded_metrics: dict | None = None,
                     current_data: list[list[float]] | None = None) -> dict:
        """Observe the active deployment; supervisor decides recovery.

        When `current_data` is supplied (recent production feature rows), the
        advanced drift engine compares it against the training dataset by
        feature (PSI + KS) and by model predictions, producing DriftReports
        that feed the performance agent and the supervisor's policy facts.
        """
        active = self.registry.active_deployment(model_name)
        if not active:
            return {"status": "NO_ACTIVE_DEPLOYMENT"}
        version_id = active["version_id"]
        passport = self.registry.load_passport(version_id)
        metrics = dict(passport.metrics)
        if degraded_metrics:
            metrics.update(degraded_metrics)
        drift_reports: list = []
        drift_summary: dict | None = None
        if current_data:
            drift_reports, drift_summary = self.run_drift_check(model_name, current_data)
            self.last_drift_status[model_name] = drift_summary
        context = {
            "subject_id": version_id,
            "version_record": self.registry.get_version(version_id),
            "passport": passport,
            "keystore": self.keystore,
            "bom": self._load_bom(self.registry.get_version(version_id)["bom_digest"]),
            "artifact_digest": active["artifact_digest"],
            "metrics": metrics,
            "drift_detected": bool(degraded_metrics) or bool(drift_reports),
            "drift_reports": [r.to_dict() for r in drift_reports],
            "drift_summary": drift_summary,
            "probe_inputs": [[0.1, -0.2], [0.5, 0.3]],
        }
        outcome = self.supervisor.run_cycle(version_id, context_override=context)
        outcome["observed_metrics"] = metrics
        if drift_summary:
            outcome["drift_summary"] = drift_summary
        self.last_observations[model_name] = outcome["report"]["observations"]
        return outcome

    def run_drift_check(self, model_name: str, current_data: list[list[float]]) -> tuple[list, dict]:
        """Feature (PSI/KS) + prediction drift of current data vs training data."""
        import numpy as np

        from qsmlops.ml.drift import DriftDetectionEngine

        active = self.registry.active_deployment(model_name)
        if not active:
            return [], {"status": "NO_ACTIVE_DEPLOYMENT", "max_severity": "NONE", "drift_count": 0}
        passport = self.registry.load_passport(active["version_id"])
        dataset_name = passport.training_info.get("dataset", model_name)
        ds = self.dataset_cache.get(dataset_name) or self._load_dataset(dataset_name)
        if ds is None:
            return [], {"status": "NO_REFERENCE_DATA", "max_severity": "NONE", "drift_count": 0}
        engine = DriftDetectionEngine()
        ref = np.asarray(ds.X, dtype=float)
        cur = np.asarray(current_data, dtype=float)
        if cur.ndim != 2 or cur.shape[1] != ref.shape[1]:
            return [], {"status": "FEATURE_MISMATCH", "max_severity": "NONE", "drift_count": 0}
        ref_preds = self._predict_matrix(model_name, ref)
        cur_preds = self._predict_matrix(model_name, cur)
        engine.set_reference(ref, predictions=ref_preds, metrics=dict(passport.metrics),
                             feature_names=ds.feature_names)
        reports = engine.detect_all(cur, current_predictions=cur_preds,
                                    current_metrics=dict(passport.metrics))
        summary = engine.get_summary(reports)
        self.ledger.append({
            "type": "drift_check", "model": model_name,
            "version_id": active["version_id"], "summary": summary,
        })
        return reports, summary

    def _predict_matrix(self, model_name: str, X) -> list[float]:
        active = self.registry.active_deployment(model_name)
        if not active:
            raise ValueError(f"no active deployment for {model_name}")
        rec = self.registry.get_version(active["version_id"])
        passport = self.registry.load_passport(active["version_id"])
        artifact = self.artifacts.get(rec["artifact_digest"])
        framework = passport.training_info.get("framework", "reference")
        if framework == "reference":
            model = json.loads(artifact.decode("utf-8"))
            weights, bias = model["weights"], model["bias"]
            return [sum(w * x for w, x in zip(weights, row)) + bias for row in X.tolist()]
        from qsmlops.ml.adapters import get_serializer

        model = get_serializer(framework).deserialize(artifact)
        return [float(p) for p in model.predict(X)]

    def _load_bom(self, bom_digest: str):
        """Load a QML-BOM by digest, tolerating on-disk corruption.

        The artifact store refuses bytes whose digest no longer matches the
        claimed address (IOError). For BOMs we still attempt to parse the raw
        bytes so agents can validate each entry and surface integrity
        findings; only unreadable or missing BOMs yield None.
        """
        from qsmlops.supplychain.bom import QMLBOM

        path = self.artifacts._path_for(bom_digest)
        if not path.exists():
            return None
        try:
            doc = json.loads(path.read_bytes().decode("utf-8"))
        except (IOError, ValueError):
            return None
        try:
            return QMLBOM.from_dict(doc)
        except Exception:
            return None

    def _auto_retrain(self, model_name: str) -> str:
        # Get the dataset name from the latest version's passport
        versions = self.registry.list_versions(model_name)
        if not versions:
            raise ValueError(f"no versions found for {model_name}")
        latest = versions[-1]
        passport = self.registry.load_passport(latest["version_id"])
        dataset_name = passport.training_info.get("dataset", f"{model_name}-data")
        framework = passport.training_info.get("framework", "reference")
        ds = self.dataset_cache.get(dataset_name) or self._load_dataset(dataset_name)
        if ds is None:
            # Fallback: try any cached dataset
            for cached_ds in self.dataset_cache.values():
                ds = cached_ds
                break
        if ds is None:
            raise ValueError(f"no dataset available for retraining {model_name}")
        result = self.train_and_register(model_name, dataset_name, dataset=ds, framework=framework)
        evaluation = self.evaluate_version(result["version_id"])
        if evaluation["decision"] == "VERIFIED":
            self.approve_and_deploy(result["version_id"])
        return result["version_id"]

    def close(self) -> None:
        self.registry.close()


def _make_train_fn(trainer):
    def fn(dataset: Dataset, **kw):
        return trainer(dataset, **kw)

    return fn
