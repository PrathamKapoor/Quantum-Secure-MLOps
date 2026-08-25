"""Migration framework: ordered, idempotent schema migrations.

Migrations are plain versioned statement bundles tracked in ``schema_migrations``.
They run in version order; each applies at most once. The registry DB used by
the model registry keeps its own bootstrap schema (created by ModelRegistry),
so platform database migrations only manage the *platform* store.

The production database requirements (encrypted at rest, quantum-safe
transport, immutable audit) will be met by swapping the engine/dialect —
migration versioning is dialect-neutral SQL applied through the engine.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from qsmlops.database.engine import DatabaseEngine

MIGRATION_TABLE = "schema_migrations"


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    statements: tuple[str, ...]


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        1,
        "create_core_tables",
        (
            """
            CREATE TABLE IF NOT EXISTS identities (
                identity_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                name TEXT NOT NULL,
                owner TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                version INTEGER NOT NULL DEFAULT 1,
                permissions TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                hash TEXT NOT NULL DEFAULT '',
                signature TEXT NOT NULL DEFAULT '',
                verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
                metadata TEXT NOT NULL DEFAULT '{}',
                UNIQUE(kind, name)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_identities_kind ON identities (kind)",
            "CREATE INDEX IF NOT EXISTS idx_identities_status ON identities (status)",
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                audit_pk INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                timestamp REAL NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                result TEXT NOT NULL,
                evidence_reference TEXT NOT NULL DEFAULT '',
                metadata TEXT NOT NULL DEFAULT '{}',
                ledger_entry_hash TEXT NOT NULL DEFAULT ''
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events (actor)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events (action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_events (resource)",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events (timestamp)",
            """
            CREATE TABLE IF NOT EXISTS object_registry (
                object_id TEXT PRIMARY KEY,
                object_type TEXT NOT NULL,
                owner TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                hash TEXT NOT NULL DEFAULT '',
                signature TEXT NOT NULL DEFAULT '',
                verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
                metadata TEXT NOT NULL DEFAULT '{}'
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_objects_type ON object_registry (object_type)",
        ),
    ),
    Migration(
        2,
        "ml_lifecycle_tables",
        (
            """
            CREATE TABLE IF NOT EXISTS datasets (
                dataset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                owner TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS dataset_versions (
                version_id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL REFERENCES datasets(dataset_id),
                version INTEGER NOT NULL,
                digest TEXT NOT NULL,
                schema_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'committed',
                security_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
                provenance_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                UNIQUE(dataset_id, version)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_dsv_dataset ON dataset_versions (dataset_id, version)",
            "CREATE INDEX IF NOT EXISTS idx_dsv_digest ON dataset_versions (digest)",
            """
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                dataset_version_id TEXT NOT NULL REFERENCES dataset_versions(version_id),
                config_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'created',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                completed_at REAL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_exp_dataset ON experiments (dataset_version_id)",
            """
            CREATE TABLE IF NOT EXISTS training_runs (
                run_id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
                dataset_version_id TEXT NOT NULL REFERENCES dataset_versions(version_id),
                model_name TEXT NOT NULL,
                framework TEXT NOT NULL DEFAULT '',
                hyperparameters_json TEXT NOT NULL DEFAULT '{}',
                metrics_json TEXT NOT NULL DEFAULT '{}',
                environment_json TEXT NOT NULL DEFAULT '{}',
                artifact_digest TEXT NOT NULL DEFAULT '',
                model_version_id TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'started',
                error TEXT NOT NULL DEFAULT '',
                started_at REAL NOT NULL,
                completed_at REAL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_run_experiment ON training_runs (experiment_id)",
            "CREATE INDEX IF NOT EXISTS idx_run_model ON training_runs (model_name)",
            """
            CREATE TABLE IF NOT EXISTS model_lineage (
                version_id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                experiment_id TEXT NOT NULL DEFAULT '',
                run_id TEXT NOT NULL DEFAULT '',
                dataset_version_id TEXT NOT NULL DEFAULT '',
                artifact_digest TEXT NOT NULL DEFAULT '',
                passport_digest TEXT NOT NULL DEFAULT '',
                bom_digest TEXT NOT NULL DEFAULT '',
                registered_at REAL NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_lineage_dataset ON model_lineage (dataset_version_id)",
            "CREATE INDEX IF NOT EXISTS idx_lineage_artifact ON model_lineage (artifact_digest)",
            """
            CREATE TABLE IF NOT EXISTS deployment_events (
                event_pk INTEGER PRIMARY KEY AUTOINCREMENT,
                deployment_id TEXT NOT NULL DEFAULT '',
                version_id TEXT NOT NULL,
                model_name TEXT NOT NULL DEFAULT '',
                action TEXT NOT NULL,
                actor TEXT NOT NULL DEFAULT '',
                packet_id TEXT NOT NULL DEFAULT '',
                previous_version_id TEXT NOT NULL DEFAULT '',
                result TEXT NOT NULL DEFAULT 'SUCCESS',
                reason TEXT NOT NULL DEFAULT '',
                at REAL NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_depl_model ON deployment_events (model_name, at)",
            "CREATE INDEX IF NOT EXISTS idx_depl_version ON deployment_events (version_id)",
            """
            CREATE TABLE IF NOT EXISTS observations (
                observation_id TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                subject_id TEXT NOT NULL DEFAULT '',
                recommendation TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                max_severity TEXT NOT NULL DEFAULT 'LOW',
                mean_confidence REAL NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_obs_subject ON observations (subject_id, created_at)",
            """
            CREATE TABLE IF NOT EXISTS findings (
                finding_id TEXT PRIMARY KEY,
                observation_id TEXT NOT NULL,
                agent TEXT NOT NULL,
                subject_id TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL,
                passed INTEGER NOT NULL,
                severity TEXT NOT NULL,
                risk TEXT NOT NULL DEFAULT '',
                detail TEXT NOT NULL DEFAULT '',
                observation_text TEXT NOT NULL DEFAULT '',
                evidence_json TEXT NOT NULL DEFAULT '[]',
                confidence REAL NOT NULL DEFAULT 0.8,
                recommendation TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_findings_subject ON findings (subject_id, name, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_findings_name ON findings (name)",
            """
            CREATE TABLE IF NOT EXISTS supervisor_decisions (
                decision_id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL DEFAULT '',
                model_name TEXT NOT NULL DEFAULT '',
                decision TEXT NOT NULL,
                risk_score REAL NOT NULL DEFAULT 0,
                rationale TEXT NOT NULL DEFAULT '',
                facts_json TEXT NOT NULL DEFAULT '{}',
                policy_decisions_json TEXT NOT NULL DEFAULT '[]',
                category_scores_json TEXT NOT NULL DEFAULT '{}',
                scores_json TEXT NOT NULL DEFAULT '{}',
                packet_id TEXT NOT NULL DEFAULT '',
                action_success INTEGER,
                verified INTEGER,
                detail TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_decision_subject ON supervisor_decisions (subject_id, created_at)",
            """
            CREATE TABLE IF NOT EXISTS recovery_actions (
                action_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL DEFAULT '',
                action TEXT NOT NULL,
                target_version_id TEXT NOT NULL DEFAULT '',
                model_name TEXT NOT NULL DEFAULT '',
                trigger_summary TEXT NOT NULL DEFAULT '',
                policy_result TEXT NOT NULL DEFAULT '',
                previous_state TEXT NOT NULL DEFAULT '',
                resulting_state TEXT NOT NULL DEFAULT '',
                execution_result TEXT NOT NULL DEFAULT '',
                verification_result TEXT NOT NULL DEFAULT '',
                detail TEXT NOT NULL DEFAULT '',
                started_at REAL NOT NULL,
                finished_at REAL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_recovery_model ON recovery_actions (model_name, started_at)",
            """
            CREATE TABLE IF NOT EXISTS security_evidence (
                evidence_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                resource_type TEXT NOT NULL DEFAULT '',
                resource_id TEXT NOT NULL DEFAULT '',
                actor TEXT NOT NULL DEFAULT '',
                result TEXT NOT NULL,
                context_json TEXT NOT NULL DEFAULT '{}',
                evidence_reference TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_secev_resource ON security_evidence (resource_type, resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_secev_kind ON security_evidence (kind)",
            """
            CREATE TABLE IF NOT EXISTS provenance_edges (
                edge_pk INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_type TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                UNIQUE(subject_type, subject_id, predicate, object_type, object_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_prov_subject ON provenance_edges (subject_type, subject_id)",
            "CREATE INDEX IF NOT EXISTS idx_prov_object ON provenance_edges (object_type, object_id)",
        ),
    ),
)


class MigrationRunner:
    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine

    def _ensure_table(self) -> None:
        self.engine.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at REAL NOT NULL
            )
            """
        )

    def applied_versions(self) -> list[int]:
        self._ensure_table()
        rows = self.engine.query_all(
            f"SELECT version FROM {MIGRATION_TABLE} ORDER BY version"
        )
        return [row["version"] for row in rows]

    def migrate(self) -> list[str]:
        """Apply all pending migrations; returns names applied this call."""
        self.engine.connect()
        self._ensure_table()
        applied = set(self.applied_versions())
        result: list[str] = []
        for migration in sorted(MIGRATIONS, key=lambda m: m.version):
            if migration.version in applied:
                continue
            for statement in migration.statements:
                self.engine.execute(statement)
            self.engine.execute(
                f"INSERT INTO {MIGRATION_TABLE} (version, name, applied_at) VALUES (?,?,?)",
                (migration.version, migration.name, time.time()),
            )
            result.append(f"{migration.version:03d}_{migration.name}")
        return result
