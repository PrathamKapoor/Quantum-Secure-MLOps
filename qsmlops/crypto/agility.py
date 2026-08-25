"""Cryptographic Agility Engine.

Manages named cipher suites (signature + KEM + hash combinations), their
lifecycle status, suite selection policy and migration planning between
suites. Algorithms are never hardcoded at call sites; everything resolves
through this engine so that a future PQC upgrade is a data change, not a
code change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from qsmlops.crypto.hashing import HASH_ALGORITHM
from qsmlops.crypto.providers import (
    KEM_PROVIDERS,
    SIGNATURE_PROVIDERS,
    ProviderError,
)

STATUS_RECOMMENDED = "recommended"
STATUS_ACCEPTABLE = "acceptable"
STATUS_DEPRECATED = "deprecated"
STATUS_EMERGENCY = "emergency"


@dataclass(frozen=True)
class CryptoSuite:
    suite_id: str
    signature_algorithm: str
    kem_algorithm: str
    hash_algorithm: str = HASH_ALGORITHM
    status: str = STATUS_RECOMMENDED
    notes: str = ""


@dataclass
class MigrationPlan:
    from_suite: str
    to_suite: str
    steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "from_suite": self.from_suite,
            "to_suite": self.to_suite,
            "steps": list(self.steps),
        }


class AgilityEngine:
    """Registry of cipher suites with selection and migration planning."""

    def __init__(self) -> None:
        self._suites: dict[str, CryptoSuite] = {}
        for sig_alg in SIGNATURE_PROVIDERS:
            for kem_alg in KEM_PROVIDERS:
                level_sig = SIGNATURE_PROVIDERS[sig_alg].security_level
                level_kem = KEM_PROVIDERS[kem_alg].security_level
                suite_id = f"QS-{level_sig}{level_kem}-{sig_alg}+{kem_alg}"
                status = STATUS_RECOMMENDED if (
                    level_sig >= 3 or level_kem >= 3
                ) else STATUS_ACCEPTABLE
                self._suites[suite_id] = CryptoSuite(
                    suite_id=suite_id,
                    signature_algorithm=sig_alg,
                    kem_algorithm=kem_alg,
                    status=status,
                )
        self.default_suite: Optional[str] = None
        recommended = [
            s for s in self._suites.values() if s.status == STATUS_RECOMMENDED
        ]
        if recommended:
            best = max(
                recommended,
                key=lambda s: (
                    SIGNATURE_PROVIDERS[s.signature_algorithm].security_level
                    + KEM_PROVIDERS[s.kem_algorithm].security_level
                ),
            )
            self.default_suite = best.suite_id
            self.default_suite_obj = best

    def register_suite(self, suite: CryptoSuite) -> None:
        self._validate_suite(suite)
        self._suites[suite.suite_id] = suite

    @staticmethod
    def _validate_suite(suite: CryptoSuite) -> None:
        if suite.signature_algorithm not in SIGNATURE_PROVIDERS:
            raise ProviderError(
                f"unknown signature algorithm {suite.signature_algorithm!r}"
            )
        if suite.kem_algorithm not in KEM_PROVIDERS:
            raise ProviderError(f"unknown KEM algorithm {suite.kem_algorithm!r}")
        if suite.hash_algorithm != HASH_ALGORITHM:
            raise ProviderError(
                f"unsupported hash {suite.hash_algorithm!r}; platform standard is {HASH_ALGORITHM}"
            )

    def get_suite(self, suite_id: str) -> CryptoSuite:
        try:
            return self._suites[suite_id]
        except KeyError as exc:
            raise ProviderError(f"unknown suite {suite_id!r}") from exc

    def select_suite(self, suite_id: Optional[str] = None) -> CryptoSuite:
        if suite_id is not None:
            return self.get_suite(suite_id)
        if self.default_suite is None:
            raise ProviderError("no suites registered")
        return self.get_suite(self.default_suite)

    def assert_usable(self, suite: CryptoSuite) -> None:
        if suite.status == STATUS_DEPRECATED:
            raise ProviderError(
                f"suite {suite.suite_id} is deprecated; migrate before new use"
            )
        if suite.status == STATUS_EMERGENCY:
            pass  # usable only under break-glass; caller must record justification
        if suite.status not in (
            STATUS_RECOMMENDED,
            STATUS_ACCEPTABLE,
            STATUS_EMERGENCY,
        ):
            raise ProviderError(f"suite {suite.suite_id} unusable (status={suite.status})")

    def mark_deprecated(self, suite_id: str) -> None:
        suite = self.get_suite(suite_id)
        self._suites[suite_id] = CryptoSuite(
            suite_id=suite.suite_id,
            signature_algorithm=suite.signature_algorithm,
            kem_algorithm=suite.kem_algorithm,
            hash_algorithm=suite.hash_algorithm,
            status=STATUS_DEPRECATED,
            notes=suite.notes,
        )

    def plan_migration(
        self, from_suite_id: str, to_suite_id: Optional[str] = None
    ) -> MigrationPlan:
        src = self.get_suite(from_suite_id)
        dst = self.select_suite(to_suite_id)
        steps = [
            f"provision keys for target suite {dst.suite_id}",
            "deploy dual-verification window (verify old + new signatures)",
            f"re-sign all passports currently signed with {src.signature_algorithm}",
            f"rotate KEM key material from {src.kem_algorithm} to {dst.kem_algorithm}",
            "mark source suite deprecated",
            "retire verification support for source suite after grace period",
        ]
        return MigrationPlan(src.suite_id, dst.suite_id, steps)

    def audit_inventory(self, signed_with: dict[str, int]) -> dict:
        """Audit a mapping of suite_id -> count of artifacts using it."""
        report: dict[str, dict] = {}
        for suite_id, count in sorted(signed_with.items()):
            suite = self._suites.get(suite_id)
            report[suite_id] = {
                "artifacts": count,
                "status": suite.status if suite else "UNKNOWN_SUITE",
                "action": (
                    "none"
                    if suite and suite.status == STATUS_RECOMMENDED
                    else "migrate"
                ),
            }
        return report
