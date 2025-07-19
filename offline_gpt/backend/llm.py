from llama_cpp import Llama
import os
from typing import List, Dict
import logging

logger = logging.getLogger("offline-gpt")

class LLMBackend:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self._load_model()
        # Store conversation history for context
        self.conversation_history: List[Dict[str, str]] = []

    def _load_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        try:
            logger.info(f"Loading GGUF model from: {self.model_path}")
            for handler in logger.handlers:
                handler.flush()
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=2048,
                verbose=False
            )
            logger.info("GGUF model loaded successfully")
            for handler in logger.handlers:
                handler.flush()
        except Exception as e:
            logger.error(f"Failed to load GGUF model: {e}")
            for handler in logger.handlers:
                handler.flush()
            raise RuntimeError(f"Failed to load LLM model: {e}")

    def chat(self, prompt: str, system_prompt: str = "You are a helpful assistant."):
        logger.info(f"Calling LLM with prompt: {prompt}")
        for handler in logger.handlers:
            handler.flush()
        if not self.model:
            raise RuntimeError("Model not loaded.")
        try:
            # Build conversation context
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.conversation_history[-10:])
            messages.append({"role": "user", "content": prompt})
            formatted_prompt = self._format_messages(messages)
            logger.info(f"Formatted prompt sent to model: {formatted_prompt}")
            for handler in logger.handlers:
                handler.flush()
            response = self.model(
                formatted_prompt,
                max_tokens=256,
                temperature=0.7,
                stop=["<|end|>", "<|user|>"],
                stream=False
            )
            logger.info(f"Model raw response: {response}")
            for handler in logger.handlers:
                handler.flush()
            if isinstance(response, dict) and 'choices' in response:
                generated_text = response['choices'][0]['text'].strip()
                # Clean up the response - remove any remaining assistant tags and extra content
                generated_text = generated_text.replace('<|assistant|>', '').strip()
                # If there are multiple responses, take only the first one
                if '<|assistant|>' in generated_text:
                    generated_text = generated_text.split('<|assistant|>')[0].strip()
            else:
                generated_text = "[Invalid response format]"
            self.conversation_history.extend([
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": generated_text}
            ])
            logger.info(f"Extracted LLM response: {generated_text}")
            for handler in logger.handlers:
                handler.flush()
            return generated_text
        except Exception as e:
            logger.error(f"LLM error: {e}")
            for handler in logger.handlers:
                handler.flush()
            return f"[LLM error: {e}]"

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Phi-3 chat template"""
        formatted = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            if role == "system":
                formatted += f"<|system|>\n{content}<|end|>\n"
            elif role == "user":
                formatted += f"<|user|>\n{content}<|end|>\n"
            elif role == "assistant":
                formatted += f"<|assistant|>\n{content}<|end|>\n"
        formatted += "<|assistant|>\n"
        return formatted 