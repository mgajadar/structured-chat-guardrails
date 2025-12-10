# structured_client.py
import json
from typing import List, Type, TypeVar, Tuple

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
    MAX_RETRIES,
    TEMPERATURE,
)
from config import validateConfig

T = TypeVar("T", bound=BaseModel)


def schemaDescription(modelClass: Type[BaseModel]) -> str:
    """
    Build a human-readable schema description from a Pydantic model.
    This is shown to the LLM so it knows exactly what JSON to produce.
    """
    schema = modelClass.model_json_schema()
    lines: List[str] = []

    title = schema.get("title", modelClass.__name__)
    lines.append(f"Schema name: {title}")
    lines.append("Type: JSON object")
    lines.append("Fields:")

    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    for fieldName, meta in properties.items():
        fieldType = meta.get("type", "object")
        fieldDesc = meta.get("description", "")
        isRequired = "required" if fieldName in required else "optional"
        lines.append(f"- {fieldName} ({fieldType}, {isRequired}): {fieldDesc}")

    return "\n".join(lines)


class StructuredChatClient:
    """
    Simple "guardrails-like" client:
    - asks the model for JSON only
    - parses JSON
    - validates against a Pydantic model
    - on failure, retries with error feedback
    """

    def __init__(
        self,
        modelName: str = OPENAI_MODEL_NAME,
        maxRetries: int = MAX_RETRIES,
        temperature: float = TEMPERATURE,
    ):
        validateConfig()
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.modelName = modelName
        self.maxRetries = maxRetries
        self.temperature = temperature

    def _makeSystemPrompt(self, modelClass: Type[BaseModel]) -> str:
        desc = schemaDescription(modelClass)
        baseInstructions = f"""
You are a strict JSON generator.

You MUST:
- Return ONLY a single JSON object, no prose.
- Ensure the JSON exactly matches the schema below.
- Never include comments or trailing commas.
- Use null for missing optional values.

{desc}
""".strip()
        return baseInstructions

    def callStructured(
        self,
        userMessage: str,
        modelClass: Type[T],
    ) -> Tuple[T, str]:
        """
        Call the LLM with enforced JSON output and validate against modelClass.

        Returns:
            (validatedModel, rawJsonText)
        Raises:
            RuntimeError if validation repeatedly fails.
        """
        systemMessage = self._makeSystemPrompt(modelClass)

        messages = [
            {"role": "system", "content": systemMessage},
            {"role": "user", "content": userMessage},
        ]

        lastErrorText = ""

        for attempt in range(1, self.maxRetries + 1):
            print(f"[structured_client] attempt {attempt}/{self.maxRetries}")

            response = self.client.chat.completions.create(
                model=self.modelName,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )

            rawContent = response.choices[0].message.content
            if rawContent is None:
                rawContent = ""

            try:
                parsed = json.loads(rawContent)
            except json.JSONDecodeError as e:
                lastErrorText = f"JSON parsing error: {e}"
                print(f"[structured_client] {lastErrorText}")
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Your previous response was not valid JSON. "
                            "Return ONLY a valid JSON object that matches the schema."
                        ),
                    }
                )
                continue

            try:
                validated = modelClass.model_validate(parsed)
                print("[structured_client] validation passed.")
                return validated, rawContent
            except ValidationError as e:
                lastErrorText = f"Pydantic validation error: {e}"
                print(f"[structured_client] {lastErrorText}")

                # Add feedback and retry
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Your previous JSON did not match the schema. "
                            "Here is the validation error:\n"
                            f"{e}\n\n"
                            "Return ONLY a corrected JSON object that matches the schema."
                        ),
                    }
                )

        raise RuntimeError(
            f"Structured output validation failed after {self.maxRetries} attempts. "
            f"Last error: {lastErrorText}"
        )
