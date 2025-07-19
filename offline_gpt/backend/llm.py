from llama_cpp import Llama
import os
from typing import Any, cast

class LLMBackend:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        try:
            self.model = Llama(model_path=self.model_path, n_ctx=2048)
        except Exception as e:
            raise RuntimeError(f"Failed to load LLM model: {e}")

    def chat(self, prompt: str, system_prompt: str = "You are a helpful assistant."):
        if not self.model:
            raise RuntimeError("Model not loaded.")
        # Simple prompt format for Phi 3 mini
        full_prompt = f"{system_prompt}\nUser: {prompt}\nAssistant:"
        try:
            output = self.model(full_prompt, max_tokens=256, stop=["User:", "Assistant:"], stream=False)
            output_dict = cast(dict, output)
            return output_dict['choices'][0]['text'].strip()
        except Exception as e:
            return f"[LLM error: {e}]" 