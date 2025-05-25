#!/usr/bin/env python
from google import genai
from config import SUPPORTED_MODELS

# Configure the client
client = genai.Client(api_key=SUPPORTED_MODELS["flash"].api_key)

# List available models
models = client.list_models()
print("Available models:")
for model in models:
    print(f"- {model.name}")
    print(f"  Supported generation methods: {model.supported_generation_methods}")
    print("")