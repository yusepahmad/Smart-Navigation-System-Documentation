"""History model for successful path searches."""


class History:
    """Stack-like container for path history."""

    def __init__(self):
        self._stack: list[list[str]] = []

    @property
    def stack(self) -> list[list[str]]:
        return self._stack

    def push(self, path: list[str]) -> None:
        if path:
            self._stack.append(path)

    def clear(self) -> None:
        self._stack.clear()

    def to_display_string(self) -> str:
        if not self._stack:
            return "(history kosong)"

        lines = []
        for idx, path in enumerate(self._stack, 1):
            lines.append(f"{idx}. {'-'.join(path)}")
        return "\n".join(lines)
