class MockProvider:
    """Deterministic, network-free provider used only by automated tests."""

    def __init__(self, response: str | None = None) -> None:
        self.response = response or "The retrieved documents describe the topic directly. [S1]"
        self.prompts: list[str] = []

    def health_check(self) -> bool:
        return True

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response