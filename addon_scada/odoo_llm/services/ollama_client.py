from ollama import Client


class OllamaClient:
    def __init__(self, model='llama3', entrypoint='http://localhost:11434'):
        self.model = model
        self.entrypoint = entrypoint

    def ask(self, prompt):
        client = Client(
            host=self.entrypoint,
        )
        response = client.chat(model=self.model, messages=[
            {"role": "user", "content": prompt}
        ])
        return response['message']['content']