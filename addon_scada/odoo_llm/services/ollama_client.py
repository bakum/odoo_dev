import json

import requests
from ollama import Client


class OllamaClient:
    def __init__(self, model='llama3', entrypoint='http://localhost:11434'):
        self.model = model
        self.entrypoint = entrypoint

    def set_context(self, messages):
        """Set context for the client, if needed."""
        client = Client(
            host=self.entrypoint,
        )
        response = client.chat(model=self.model, messages=messages)
        return response['message']['content']

    def ask(self, prompt, history=None):
        if history is None:
            history = []
        client = Client(
            host=self.entrypoint,
        )
        messages = []
        if history is not None:
            messages = history
        messages.append({"role": "user", "content": prompt})
        response = client.chat(model=self.model, messages=messages, options={
            "temperature": 0.7,
            # "top_p": 0.9,
            "max_tokens": 4096,
            # "stop": ["</s>"],  # опционально
        })
        return response['message']['content']

    def stream_text(self, prompt, history=None):
        url = f"{self.entrypoint}/api/chat"
        headers = {"Content-Type": "application/json"}
        messages = history[:] if history else []
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        with requests.post(url, headers=headers, json=payload, stream=True) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        # Здесь ключ зависит от структуры ответа
                        yield data.get("response") or data.get("message", {}).get("content", "")
                    except Exception:
                        continue
