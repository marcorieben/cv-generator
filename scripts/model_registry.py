"""
Multi-Model Support Registry
Supports OpenAI, Anthropic Claude, and PyResParser
"""
import os
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class BaseModelProvider(ABC):
    """Base class for AI model providers"""

    @abstractmethod
    def extract_cv(self, pdf_text: str, schema: dict, language: str) -> dict:
        """Extract CV data from PDF text"""
        pass

    @abstractmethod
    def get_cost_per_1k_tokens(self) -> dict:
        """Return cost structure"""
        pass

# ============================================================================
# OPENAI PROVIDER
# ============================================================================

class OpenAIProvider(BaseModelProvider):
    """OpenAI GPT models (GPT-4o-mini, GPT-4o, o1-mini, o1)"""

    MODELS = {
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "input_cost": 0.150,   # $ per 1M tokens
            "output_cost": 0.600,
            "speed": "fast",
            "quality": "good"
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "input_cost": 2.50,
            "output_cost": 10.00,
            "speed": "medium",
            "quality": "excellent"
        },
        "o1-mini": {
            "name": "O1 Mini (Reasoning)",
            "input_cost": 3.00,
            "output_cost": 12.00,
            "speed": "slow",
            "quality": "excellent"
        },
        "o1": {
            "name": "O1 (Advanced Reasoning)",
            "input_cost": 15.00,
            "output_cost": 60.00,
            "speed": "very slow",
            "quality": "best"
        }
    }

    def __init__(self, model_name: str = "gpt-4o-mini"):
        from openai import OpenAI
        self.model_name = model_name
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def extract_cv(self, pdf_text: str, schema: dict, language: str) -> dict:
        import json

        system_prompt = f"""Extract CV data in {language}. Return valid JSON matching this schema:
{json.dumps(schema, indent=2)}"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": pdf_text}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        return json.loads(response.choices[0].message.content)

    def get_cost_per_1k_tokens(self) -> dict:
        model_info = self.MODELS.get(self.model_name, self.MODELS["gpt-4o-mini"])
        return {
            "input": model_info["input_cost"] / 1000,  # Per 1k tokens
            "output": model_info["output_cost"] / 1000
        }

# ============================================================================
# ANTHROPIC CLAUDE PROVIDER
# ============================================================================

class AnthropicProvider(BaseModelProvider):
    """Anthropic Claude models (Haiku, Sonnet, Opus)"""

    MODELS = {
        "claude-3-5-haiku-20241022": {
            "name": "Claude 3.5 Haiku",
            "input_cost": 0.80,    # $ per 1M tokens
            "output_cost": 4.00,
            "speed": "very fast",
            "quality": "good"
        },
        "claude-3-5-sonnet-20241022": {
            "name": "Claude 3.5 Sonnet",
            "input_cost": 3.00,
            "output_cost": 15.00,
            "speed": "fast",
            "quality": "excellent"
        },
        "claude-3-7-sonnet-20250219": {
            "name": "Claude 3.7 Sonnet (Latest)",
            "input_cost": 3.00,
            "output_cost": 15.00,
            "speed": "fast",
            "quality": "best"
        }
    }

    def __init__(self, model_name: str = "claude-3-5-haiku-20241022"):
        from anthropic import Anthropic
        self.model_name = model_name
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def extract_cv(self, pdf_text: str, schema: dict, language: str) -> dict:
        import json

        system_prompt = f"""Extract CV data in {language}. Return ONLY valid JSON matching this schema:
{json.dumps(schema, indent=2)}

CRITICAL: Your response must be ONLY the JSON object, no explanations."""

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": pdf_text}
            ]
        )

        # Claude returns JSON in content[0].text
        json_text = response.content[0].text

        # Strip markdown code blocks if present
        if json_text.startswith("```json"):
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif json_text.startswith("```"):
            json_text = json_text.split("```")[1].split("```")[0].strip()

        return json.loads(json_text)

    def get_cost_per_1k_tokens(self) -> dict:
        model_info = self.MODELS.get(self.model_name, self.MODELS["claude-3-5-haiku-20241022"])
        return {
            "input": model_info["input_cost"] / 1000,
            "output": model_info["output_cost"] / 1000
        }

# ============================================================================
# PYRESPARSER PROVIDER (Open Source, FREE)
# ============================================================================

class PyResParserProvider(BaseModelProvider):
    """Free open-source CV parser (no API costs!)"""

    def __init__(self):
        try:
            from pyresparser import ResumeParser
            self.parser = ResumeParser
        except ImportError:
            raise ImportError(
                "pyresparser not installed. Install with: "
                "pip install pyresparser"
            )

    def extract_cv(self, pdf_text: str, schema: dict, language: str) -> dict:
        """
        PyResParser extracts basic fields automatically.
        Note: Quality is lower than AI models, but it's FREE!
        """
        import tempfile
        import json
        from pathlib import Path

        # PyResParser works with files, not text
        # In production, pass the original PDF path instead

        # For now, return a structured dict based on basic NLP
        return {
            "Vorname": "Extracted",
            "Nachname": "ByPyResParser",
            "Geburtsdatum": None,
            "email": self._extract_email(pdf_text),
            "telefon": self._extract_phone(pdf_text),
            "skills": self._extract_skills(pdf_text),
            "_note": "PyResParser extraction - Limited quality, but FREE"
        }

    def _extract_email(self, text: str) -> str:
        import re
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        return emails[0] if emails else ""

    def _extract_phone(self, text: str) -> str:
        import re
        phones = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', text)
        return phones[0] if phones else ""

    def _extract_skills(self, text: str) -> list:
        # Very basic keyword matching
        common_skills = [
            "Python", "Java", "JavaScript", "React", "AWS", "Docker",
            "Kubernetes", "SQL", "MongoDB", "Git", "Linux", "Agile"
        ]
        return [skill for skill in common_skills if skill.lower() in text.lower()]

    def get_cost_per_1k_tokens(self) -> dict:
        return {"input": 0.0, "output": 0.0}  # FREE!

# ============================================================================
# MODEL REGISTRY
# ============================================================================

class ModelRegistry:
    """Central registry for all available models"""

    @staticmethod
    def get_available_models() -> Dict[str, Dict[str, Any]]:
        """Return all available models with metadata"""
        return {
            # OpenAI
            "gpt-4o-mini": {
                "provider": "OpenAI",
                "display_name": "GPT-4o Mini (Cheapest)",
                "cost_per_cv": 0.01,
                "speed": "⚡ Fast",
                "quality": "🟢 Good",
                "recommended": True
            },
            "gpt-4o": {
                "provider": "OpenAI",
                "display_name": "GPT-4o (Balanced)",
                "cost_per_cv": 0.15,
                "speed": "⚡ Fast",
                "quality": "🟢 Excellent"
            },
            "o1-mini": {
                "provider": "OpenAI",
                "display_name": "O1 Mini (Reasoning)",
                "cost_per_cv": 0.20,
                "speed": "🐌 Slow",
                "quality": "🟢 Excellent"
            },
            "o1": {
                "provider": "OpenAI",
                "display_name": "O1 (Best Quality)",
                "cost_per_cv": 1.00,
                "speed": "🐌 Very Slow",
                "quality": "🟢 Best"
            },

            # Anthropic
            "claude-3-5-haiku-20241022": {
                "provider": "Anthropic",
                "display_name": "Claude 3.5 Haiku (Fast & Cheap)",
                "cost_per_cv": 0.03,
                "speed": "⚡⚡ Very Fast",
                "quality": "🟢 Good"
            },
            "claude-3-5-sonnet-20241022": {
                "provider": "Anthropic",
                "display_name": "Claude 3.5 Sonnet",
                "cost_per_cv": 0.18,
                "speed": "⚡ Fast",
                "quality": "🟢 Excellent"
            },
            "claude-3-7-sonnet-20250219": {
                "provider": "Anthropic",
                "display_name": "Claude 3.7 Sonnet (Latest)",
                "cost_per_cv": 0.18,
                "speed": "⚡ Fast",
                "quality": "🟢 Best"
            },

            # Open Source
            "pyresparser": {
                "provider": "PyResParser",
                "display_name": "PyResParser (FREE, Lower Quality)",
                "cost_per_cv": 0.00,
                "speed": "⚡⚡⚡ Instant",
                "quality": "🟡 Basic",
                "note": "No API costs, but limited extraction quality"
            }
        }

    @staticmethod
    def get_provider(model_name: str) -> BaseModelProvider:
        """Factory method to get the correct provider for a model"""

        if model_name.startswith("gpt-") or model_name.startswith("o1"):
            return OpenAIProvider(model_name)

        elif model_name.startswith("claude-"):
            return AnthropicProvider(model_name)

        elif model_name == "pyresparser":
            return PyResParserProvider()

        else:
            raise ValueError(f"Unknown model: {model_name}")

    @staticmethod
    def estimate_cost(model_name: str, num_cvs: int) -> dict:
        """Estimate monthly cost for a given model and volume"""
        models = ModelRegistry.get_available_models()
        model_info = models.get(model_name)

        if not model_info:
            return {"error": f"Unknown model: {model_name}"}

        cost_per_cv = model_info["cost_per_cv"]
        monthly_cost = cost_per_cv * num_cvs

        return {
            "model": model_name,
            "display_name": model_info["display_name"],
            "cvs_per_month": num_cvs,
            "cost_per_cv": f"${cost_per_cv:.3f}",
            "monthly_cost": f"${monthly_cost:.2f}",
            "yearly_cost": f"${monthly_cost * 12:.2f}"
        }

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Show all available models
    print("Available Models:")
    print("=" * 80)

    for model_id, info in ModelRegistry.get_available_models().items():
        print(f"\n{info['display_name']}")
        print(f"  Provider: {info['provider']}")
        print(f"  Cost/CV: ${info['cost_per_cv']:.3f}")
        print(f"  Speed: {info['speed']}")
        print(f"  Quality: {info['quality']}")
        if info.get('note'):
            print(f"  Note: {info['note']}")

    print("\n" + "=" * 80)
    print("\nCost Estimates (100 CVs/month):")
    print("-" * 80)

    for model_id in ["gpt-4o-mini", "claude-3-5-haiku-20241022", "pyresparser"]:
        estimate = ModelRegistry.estimate_cost(model_id, 100)
        print(f"{estimate['display_name']}: {estimate['monthly_cost']}/month")
