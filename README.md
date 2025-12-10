# Structured Chat Guardrails

A small, CLI-only project that turns free-form user text into **strict, validated
JSON** using an LLM, plus Pydantic validation and automatic retries.

It behaves like a lightweight "guardrails" layer:

- Instructs the model to reply with **JSON only**
- Parses the JSON
- Validates it against a **Pydantic schema**
- On failure, sends the validation error back to the model and retries

## Features

- OpenAI Chat API with `response_format={"type": "json_object"}`
- Pydantic schema (`ConversationAnalysis`) describing:
  - summary
  - intent
  - sentiment
  - action items (with owner, due date, priority)
  - risk level and follow-up flag
- Automatic retry loop on invalid JSON or schema mismatch
- Simple CLI interface

## Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your_key_here"
