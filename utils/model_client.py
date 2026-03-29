import json
import subprocess
from typing import Optional

import requests


class OllamaClient:
    """Lightweight client for local Ollama inference."""

    def __init__(self, model: str, host: str = "http://127.0.0.1:11434") -> None:
        self.model = model
        self.host = host.rstrip("/")

    def _api_generate(self, prompt: str, temperature: float, num_predict: int) -> Optional[str]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }

        try:
            response = requests.post(
                f"{self.host}/api/generate",
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            return (result.get("response") or "").strip()
        except requests.RequestException:
            return None

    def _cli_generate(self, prompt: str) -> Optional[str]:
        try:
            process = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt,
                text=True,
                capture_output=True,
                check=False,
                timeout=180,
            )
            if process.returncode != 0:
                return None
            return process.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None

    def generate(self, prompt: str, temperature: float = 0.1, num_predict: int = 220) -> str:
        """Generate text using local Ollama API with CLI fallback."""
        api_result = self._api_generate(prompt=prompt, temperature=temperature, num_predict=num_predict)
        if api_result:
            return api_result

        cli_result = self._cli_generate(prompt=prompt)
        if cli_result:
            return cli_result

        raise RuntimeError(
            "Unable to generate response from Ollama. Ensure Ollama is installed, running, and the model is pulled."
        )
