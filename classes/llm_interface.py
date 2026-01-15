import requests

class GPTSession:
    def __init__(self, api_key: str, model: str = "gpt-4.1", base_url: str = "https://api.openai.com/v1/chat/completions"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Store conversation history
        self.messages = []

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})

    def chat(self, user_input: str, temperature: float = 0.7, max_tokens: int = 2000):
        """Send user input to GPT and return the response, while updating history."""
        # Add user message
        self.add_message("user", user_input)

        payload = {
            "model": self.model,
            "messages": self.messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(self.base_url, headers=self.headers, json=payload)
        
        if(response.status_code != 200):
            print(response.text)
            reply = {
            "response": f"Error: {response.status_code} - {response.text}",
            "status_code": response.status_code
        }
        else:
            response.raise_for_status()
            data = response.json()

            reply = data["choices"][0]["message"]["content"]

            # Add assistant reply to history
            self.add_message("assistant", reply)

            reply = {
                "response": reply,
                "usage": data['usage']['total_tokens'],
                "status_code": response.status_code
            }

        print(f"GPT Response: {reply['response']}\nUsage: {reply['usage']} tokens\nStatus Code: {reply['status_code']}")
        return reply

    def reset(self):
        """Clear conversation history but keep system prompt."""
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
