import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import ProviderError


class OllamaProvider:
    """Local-only Ollama provider using Ollama's current /api/generate endpoint."""

    def __init__(self, base_url: str, model: str, temperature: float = 0.1, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def health_check(self) -> bool:
        try:
            response = self._request("/api/tags", {}, timeout=5)
            models = response.get("models", [])
            return any(model.get("name") == self.model or model.get("model") == self.model for model in models)
        except ProviderError:
            return False

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        try:
            response = self._request("/api/generate", payload, timeout=self.timeout)
        except ProviderError as error:
            raise ProviderError(f"Ollama generation failed for model '{self.model}': {error}") from error
        text = response.get("response")
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("Ollama returned a malformed or empty response")
        return text.strip()

    def _request(self, path: str, payload: dict, timeout: int) -> dict:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8") if payload else None,
            headers={"Content-Type": "application/json"},
            method="POST" if payload else "GET",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code == 404:
                raise ProviderError(f"Ollama model or endpoint not found: {detail[:200]}") from error
            raise ProviderError(f"Ollama HTTP {error.code}: {detail[:200]}") from error
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ProviderError(f"Ollama is unavailable at {self.base_url}: {error}") from error