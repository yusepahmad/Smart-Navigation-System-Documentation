"""Domain models for navigation result."""

from dataclasses import dataclass


@dataclass
class QueryResult:
    start: str
    end: str
    path: list[str]

    @property
    def distance(self) -> int:
        return len(self.path) - 1
