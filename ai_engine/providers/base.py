from typing import Protocol


class ProviderError(RuntimeError):
    """Raised when a local model provider cannot complete a request."""


class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str: ...
    def health_check(self) -> bool: ...