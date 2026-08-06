"""AI registry facts and peer-local capability execution."""

from .contracts import (
  AICapabilityUnavailableError,
  AIDialectAdapter,
  AIFeatureUnavailableError,
  AIModelDisabledError,
  AIModelNotFoundError,
  AIOutputContractError,
  AIProviderDisabledError,
  AIProviderNotFoundError,
  DuplicateAIDialectRegistrationError,
  InvalidAIProviderConfigError,
  UnknownAIDialectError,
)
from .main import AIManager

# Import installed core dialects only after AIManager exists so decorators register.
from .dialects import OpenAICompatibleConfig, OpenAICompatibleDialect

__all__ = [
  "AICapabilityUnavailableError",
  "AIDialectAdapter",
  "AIFeatureUnavailableError",
  "AIManager",
  "AIModelDisabledError",
  "AIModelNotFoundError",
  "AIOutputContractError",
  "AIProviderDisabledError",
  "AIProviderNotFoundError",
  "DuplicateAIDialectRegistrationError",
  "InvalidAIProviderConfigError",
  "OpenAICompatibleConfig",
  "OpenAICompatibleDialect",
  "UnknownAIDialectError",
]
