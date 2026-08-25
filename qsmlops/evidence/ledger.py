"""Append-only, hash-chained evidence ledger.

Every entry embeds the hash of its predecessor; the chain head is a commitment
over the full operational history. Any retroactive edit breaks the chain and is
detected by `verify_chain`.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Iterator

from qsmlops.crypto.hashing import sha3_hex
from qsmlops.evidence.packet import VerificationPacket

GENESIS_PREV = "0" * 64


class LedgerError(Exception):
    pass


class EvidenceLedger:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def append(self, record: dict) -> dict:
        with self._lock:
            entries = self._entries()
            prev_hash = entries[-1]["entry_hash"] if entries else GENESIS_PREV
            body = {
                "seq": len(entries),
                "timestamp": time.time(),
                "prev_hash": prev_hash,
                "record": record,
            }
            entry_hash = sha3_hex(
                json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
            )
            entry = {**body, "entry_hash": entry_hash}
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
            return entry

    def append_packet(self, packet: VerificationPacket) -> dict:
        return self.append(
            {
                "type": "verification_packet",
                "packet_id": packet.packet_id,
                "digest": packet.digest(),
                "objective": packet.objective,
                "actor": packet.actor,
                "decision": packet.decision,
            }
        )

    def verify_chain(self) -> tuple[bool, str]:
        entries = self._entries()
        prev = GENESIS_PREV
        for i, e in enumerate(entries):
            if e["prev_hash"] != prev:
                return False, f"chain break at entry {i}"
            body = {
                "seq": e["seq"],
                "timestamp": e["timestamp"],
                "prev_hash": e["prev_hash"],
                "record": e["record"],
            }
            expected = sha3_hex(
                json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
            )
            if expected != e["entry_hash"]:
                return False, f"hash mismatch at entry {i} (content modified)"
            if e["seq"] != i:
                return False, f"sequence gap at entry {i}"
            prev = e["entry_hash"]
        return True, f"chain intact ({len(entries)} entries)"

    def head(self) -> str:
        entries = self._entries()
        return entries[-1]["entry_hash"] if entries else GENESIS_PREV

    def iter_entries(self) -> Iterator[dict]:
        return iter(self._entries())

    def find_by_packet(self, packet_id: str) -> dict | None:
        for entry in self._entries():
            if entry.get("record", {}).get("packet_id") == packet_id:
                return entry
        return None
