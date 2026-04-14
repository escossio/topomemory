#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, Sequence

EMBEDDING_DIMENSIONS = 128
DEFAULT_EMBEDDING_PROVIDER = "hash"
DEFAULT_HASH_EMBEDDING_MODEL = "topomemory-hash-embedding-v1"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "TOPOMEMORY_EMBEDDING_PROVIDER"
EMBEDDING_MODEL_ENV = "TOPOMEMORY_EMBEDDING_MODEL"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_BASE_URL_ENV = "OPENAI_BASE_URL"
EXTERNAL_EMBEDDING_ENDPOINT_ENV = "TOPOMEMORY_EXTERNAL_EMBEDDING_ENDPOINT"
EXTERNAL_EMBEDDING_API_KEY_ENV = "TOPOMEMORY_EXTERNAL_EMBEDDING_API_KEY"
EXTERNAL_EMBEDDING_MODEL_ENV = "TOPOMEMORY_EXTERNAL_EMBEDDING_MODEL"

TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingProviderError(RuntimeError):
    pass


class EmbeddingProvider(Protocol):
    def model_name(self) -> str: ...

    def embed_text(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


def format_value(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    text = str(value).strip()
    return text if text else "none"


def tokenize_text(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def token_features(text: str) -> list[str]:
    tokens = tokenize_text(text)
    features: list[str] = []
    features.extend(tokens)
    features.extend(f"{left}_{right}" for left, right in zip(tokens, tokens[1:]))
    features.extend(f"{left}_{middle}_{right}" for left, middle, right in zip(tokens, tokens[1:], tokens[2:]))
    return features


def vector_literal(values: Sequence[float]) -> str:
    return "[" + ",".join(f"{value:.6f}" for value in values) + "]"


def _hash_embed(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    vector = [0.0] * dimensions
    features = token_features(text)
    if not features:
        return vector

    for feature in features:
        digest = hashlib.sha256(feature.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        weight = 1.0
        if "_" in feature:
            weight = 0.75
        if feature.count("_") >= 2:
            weight = 0.5
        vector[index] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


@dataclass(frozen=True, slots=True)
class HashEmbeddingProvider:
    model: str = DEFAULT_HASH_EMBEDDING_MODEL

    def model_name(self) -> str:
        return self.model

    def embed_text(self, text: str) -> list[float]:
        return _hash_embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


@dataclass(frozen=True, slots=True)
class OpenAIEmbeddingProvider:
    model: str = DEFAULT_OPENAI_EMBEDDING_MODEL
    dimensions: int = EMBEDDING_DIMENSIONS
    api_key_env: str = OPENAI_API_KEY_ENV
    base_url_env: str = OPENAI_BASE_URL_ENV
    api_key: str | None = None
    base_url: str | None = None

    @classmethod
    def from_env(cls) -> "OpenAIEmbeddingProvider":
        api_key = os.environ.get(OPENAI_API_KEY_ENV)
        if not api_key:
            raise EmbeddingProviderError(
                f"provider openai solicitado sem configuração mínima: faltam {OPENAI_API_KEY_ENV}."
            )
        model = os.environ.get(EMBEDDING_MODEL_ENV) or DEFAULT_OPENAI_EMBEDDING_MODEL
        base_url = os.environ.get(OPENAI_BASE_URL_ENV) or None
        return cls(model=model, api_key=api_key, base_url=base_url)

    def model_name(self) -> str:
        return self.model

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - environment dependency
            raise EmbeddingProviderError("pacote openai não está instalado no ambiente") from exc
        client_kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        return OpenAI(**client_kwargs)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        client = self._client()
        response = client.embeddings.create(model=self.model, input=texts, dimensions=self.dimensions)
        return [list(item.embedding) for item in response.data]

    def embed_text(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]


@dataclass(frozen=True, slots=True)
class ExternalEmbeddingProviderStub:
    endpoint_env: str = EXTERNAL_EMBEDDING_ENDPOINT_ENV
    api_key_env: str = EXTERNAL_EMBEDDING_API_KEY_ENV
    model_env: str = EXTERNAL_EMBEDDING_MODEL_ENV
    model: str | None = None

    @classmethod
    def from_env(cls) -> "ExternalEmbeddingProviderStub":
        endpoint = os.environ.get(EXTERNAL_EMBEDDING_ENDPOINT_ENV)
        api_key = os.environ.get(EXTERNAL_EMBEDDING_API_KEY_ENV)
        model = os.environ.get(EXTERNAL_EMBEDDING_MODEL_ENV)
        missing = [name for name, value in ((EXTERNAL_EMBEDDING_ENDPOINT_ENV, endpoint), (EXTERNAL_EMBEDDING_API_KEY_ENV, api_key)) if not value]
        if missing:
            raise EmbeddingProviderError(
                "provider externo solicitado sem configuração mínima: faltam "
                + ", ".join(missing)
                + ". Configure as variáveis necessárias antes de habilitar um provider real."
            )
        return cls(model=model)

    def model_name(self) -> str:
        return self.model or "external-embedding-provider-stub"

    def _fail(self) -> None:
        raise EmbeddingProviderError(
            "provider externo stub selecionado. Esta árvore ainda não implementa um adaptador real; "
            "o provider externo só pode ser usado quando a integração concreta for adicionada."
        )

    def embed_text(self, text: str) -> list[float]:
        self._fail()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._fail()


def get_embedding_provider() -> EmbeddingProvider:
    provider_name = os.environ.get(EMBEDDING_PROVIDER_ENV, DEFAULT_EMBEDDING_PROVIDER).strip().lower()
    model_override = os.environ.get(EMBEDDING_MODEL_ENV)

    if provider_name in {"hash", "default"}:
        return HashEmbeddingProvider(model=model_override or DEFAULT_HASH_EMBEDDING_MODEL)

    if provider_name in {"openai", "real", "remote"}:
        provider = OpenAIEmbeddingProvider.from_env()
        if model_override:
            return OpenAIEmbeddingProvider(
                model=model_override,
                dimensions=provider.dimensions,
                api_key_env=provider.api_key_env,
                base_url_env=provider.base_url_env,
                api_key=provider.api_key,
                base_url=provider.base_url,
            )
        return provider

    if provider_name in {"external", "external-stub", "stub"}:
        provider = ExternalEmbeddingProviderStub.from_env()
        if model_override:
            return ExternalEmbeddingProviderStub(
                endpoint_env=provider.endpoint_env,
                api_key_env=provider.api_key_env,
                model_env=provider.model_env,
                model=model_override,
            )
        return provider

    raise EmbeddingProviderError(
        f"provider desconhecido: {provider_name}. Use '{DEFAULT_EMBEDDING_PROVIDER}' ou 'openai'."
    )
