"""
====================================================================
NEA28 MACHINE LEARNING FEATURE BUILDER
Module:
    ml_feature_builder.py

Purpose
-------
The Feature Builder converts analysis engine outputs into
machine-learning-ready numerical feature vectors.

This module intentionally contains NO hardcoded dependencies on
analysis engines.

Instead, analysis engines register themselves as feature providers.

Architecture
------------
Analysis Engine
        │
        ▼
Feature Provider Plugin
        │
        ▼
Feature Builder
        │
        ▼
Normalized Feature Vector
        │
        ├── ML Predictor
        ├── ML Trainer
        ├── SQLite Storage
        └── Future AI Modules

Author:
    NEA28 Architecture

====================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ================================================================
# Feature Metadata
# ================================================================

@dataclass
class FeatureDefinition:
    """
    Describes a single ML feature.
    """

    name: str
    dtype: str = "float"
    description: str = ""
    default: float = 0.0


# ================================================================
# Plugin Interface
# ================================================================

class FeatureProvider(ABC):
    """
    Base class for every analysis engine.

    Every engine supplies features through this interface.

    No assumptions are made regarding
        candlesticks
        bill williams
        wyckoff
        elliott
        risk
        etc.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def feature_schema(self) -> List[FeatureDefinition]:
        """
        Return list of supported features.
        """
        pass

    @abstractmethod
    def build_features(self) -> Dict[str, Any]:
        """
        Return feature dictionary.

        Example

        {
            "bullish_engulfing":1,
            "trend_strength":0.82,
            ...
        }
        """
        pass


# ================================================================
# Registry
# ================================================================

class FeatureRegistry:
    """
    Stores every registered feature provider.
    """

    def __init__(self):

        self.providers: Dict[str, FeatureProvider] = {}

    def register(self, provider: FeatureProvider):

        logger.info("Registering provider: %s", provider.provider_name)

        self.providers[provider.provider_name] = provider

    def unregister(self, provider_name: str):

        self.providers.pop(provider_name, None)

    def clear(self):

        self.providers.clear()

    def get_provider(self, name: str):

        return self.providers.get(name)

    def all_providers(self):

        return list(self.providers.values())


# ================================================================
# Normalization Engine
# ================================================================

class FeatureNormalizer:
    """
    Performs normalization.

    Initial implementation is intentionally lightweight.

    Future versions may include:

        Min-Max Scaling

        Z-Score

        Robust Scaling

        Percentile Scaling

        Learned Scaling
    """

    def normalize(self, value):

        if value is None:
            return 0.0

        if isinstance(value, bool):
            return float(value)

        if isinstance(value, (int, float)):
            return float(value)

        return value


# ================================================================
# Validation
# ================================================================

class FeatureValidator:
    """
    Ensures every vector remains consistent.
    """

    def validate(
        self,
        features: Dict[str, Any]
    ) -> bool:

        if not isinstance(features, dict):
            return False

        return True


# ================================================================
# Missing Value Handler
# ================================================================

class MissingValueHandler:

    def fill(
        self,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:

        cleaned = {}

        for k, v in features.items():

            cleaned[k] = 0.0 if v is None else v

        return cleaned


# ================================================================
# Feature Builder
# ================================================================

class MLFeatureBuilder:
    """
    Central feature construction engine.

    Workflow

        Providers

            ↓

        Collect Features

            ↓

        Validate

            ↓

        Fill Missing Values

            ↓

        Normalize

            ↓

        Ordered Feature Vector
    """

    def __init__(self):

        self.registry = FeatureRegistry()

        self.normalizer = FeatureNormalizer()

        self.validator = FeatureValidator()

        self.missing_handler = MissingValueHandler()

    # ------------------------------------------------------------

    def register_provider(
        self,
        provider: FeatureProvider
    ):

        self.registry.register(provider)

    # ------------------------------------------------------------

    def unregister_provider(
        self,
        provider_name: str
    ):

        self.registry.unregister(provider_name)

    # ------------------------------------------------------------

    def collect_features(self) -> Dict[str, Any]:

        feature_dict = {}

        for provider in self.registry.all_providers():

            try:

                data = provider.build_features()

                if data:

                    feature_dict.update(data)

            except Exception as exc:

                logger.exception(
                    "Provider failed: %s",
                    provider.provider_name
                )

        return feature_dict

    # ------------------------------------------------------------

    def build_feature_vector(self):

        raw = self.collect_features()

        if not self.validator.validate(raw):

            raise ValueError("Feature validation failed.")

        raw = self.missing_handler.fill(raw)

        normalized = {}

        for key, value in raw.items():

            normalized[key] = self.normalizer.normalize(value)

        ordered_keys = sorted(normalized.keys())

        vector = [normalized[k] for k in ordered_keys]

        return {

            "feature_names": ordered_keys,

            "feature_map": normalized,

            "feature_vector": vector,

            "feature_count": len(vector)
        }


# ================================================================
# Export Interface
# ================================================================

class FeatureExporter:
    """
    Export feature vectors.

    This class intentionally contains no storage implementation.

    Future plugins may export to

        SQLite

        CSV

        NumPy

        Pandas

        PyTorch

        TensorFlow

        ONNX

        Remote Prediction API
    """

    def export(self, feature_package):

        raise NotImplementedError(
            "Exporter plugin not implemented."
        )


# ================================================================
# Example Plugin
# ================================================================

class ExampleFeatureProvider(FeatureProvider):

    @property
    def provider_name(self):

        return "Example"

    def feature_schema(self):

        return [

            FeatureDefinition(
                "example_signal",
                "float",
                "Example feature"
            ),

            FeatureDefinition(
                "trend_strength"
            )
        ]

    def build_features(self):

        return {

            "example_signal": 1,

            "trend_strength": 0.83
        }


# ================================================================
# Demonstration
# ================================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    builder = MLFeatureBuilder()

    builder.register_provider(
        ExampleFeatureProvider()
    )

    package = builder.build_feature_vector()

    print("\nFeature Package\n")

    for k, v in package.items():

        print(k)

        print(v)

        print()