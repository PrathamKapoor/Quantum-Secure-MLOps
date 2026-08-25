from qsmlops.config import PlatformConfig
from qsmlops.registry.registry import ModelRegistry
from qsmlops.artifacts.store import ArtifactStore
from qsmlops.crypto.keys import KeyStore
from qsmlops.evidence.ledger import EvidenceLedger

# We'll create a singleton instance of the registry
_registry = None

def get_registry():
    global _registry
    if _registry is None:
        # We'll use a temporary directory for the config, but we want to use the actual research system's data.
        # However, we don't want to overwrite the existing data. We'll point to the existing directories.
        # We assume the research system is installed in the default location (in the user's home) or we can use the current environment.
        # For simplicity, we'll use the default config which points to the user's home directory.
        # But note: the research system might have been run in a different location.
        # We'll rely on the fact that the research system's data is in the default location (~/.qsmlops).
        # If we are running in the same environment as the research system, this should work.
        config = PlatformConfig()
        artifacts = ArtifactStore(config.artifacts_dir)
        keystore = KeyStore(config.keys_dir)
        ledger = EvidenceLedger(config.ledger_path)
        _registry = ModelRegistry(
            config.registry_path, artifacts, keystore, ledger
        )
    return _registry

def get_models():
    registry = get_registry()
    # Get all versions for all models
    all_versions = registry.list_versions(None)
    if not all_versions:
        return []
    # Group by model_name
    models_dict = {}
    for version_info in all_versions:
        model_name = version_info["model_name"]
        if model_name not in models_dict:
            models_dict[model_name] = []
        models_dict[model_name].append(version_info)
    # For each model, take the latest version (last in the list because they are ordered by version)
    models = []
    for model_name, versions in models_dict.items():
        # The versions are sorted by version ascending, so the last one is the latest
        latest_version = versions[-1]
        # Get the passport for the latest version to get more details
        passport = registry.load_passport(latest_version["version_id"])
        # Get the registry record for the latest version
        record = registry.get_version(latest_version["version_id"])
        model_info = {
            "target": model_name.lower(),  # We assume the model name is the target (LOAD, WIND, PV) and we want lowercase
            "model_name": model_name,
            "feature_set": passport.training_info.get("feature_set", "unknown") if passport.training_info else "unknown",
            "fingerprint": latest_version["version_id"],  # We use the version_id as a fingerprint for now
            "lifecycle_state": record["state"]
        }
        models.append(model_info)
    return models

def get_versions(model_name: str) -> list[dict]:
    """All registered versions for one model name (oldest first)."""
    registry = get_registry()
    return registry.list_versions(model_name)


def get_version_detail(model_name: str, version_id: str) -> dict | None:
    """Registry record plus safe passport fields for a single version."""
    registry = get_registry()
    record = registry.find_version(model_name, _version_int_or_none(version_id)) \
        if version_id.isdigit() else None
    if record is None:
        # Also allow lookup directly by version_id.
        try:
            candidate = registry.get_version(version_id)
        except Exception:
            candidate = None
        if not candidate or candidate.get("model_name") != model_name:
            return None
        record = candidate
    detail = dict(record)
    try:
        passport = registry.load_passport(record["version_id"])
        detail["passport_id"] = getattr(passport, "passport_id", None)
        training_info = getattr(passport, "training_info", None) or {}
        detail["feature_set"] = (
            training_info.get("feature_set")
            if isinstance(training_info, dict) else None
        ) or "unknown"
        sig = getattr(passport, "signature", None)
        detail["signature_suite"] = getattr(sig, "suite_id", None)
        detail["signed_by"] = getattr(sig, "signer_key_id", None)
    except Exception:
        detail.setdefault("feature_set", "unknown")
    return detail


def _version_int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
