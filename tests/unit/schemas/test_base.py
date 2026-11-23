"""Unit tests for EonBaseModel foundation."""

import pytest
from pydantic import Field, ValidationError

from eon.schemas.base import EonBaseModel


class SampleModel(EonBaseModel):
    name: str
    count: int = Field(ge=0)
    optional_tag: str | None = None


def test_base_model_valid_construction() -> None:
    """AC-1.2-01: Verify valid model instantiation and access."""
    m = SampleModel(name="test", count=42)
    assert m.name == "test"
    assert m.count == 42
    assert m.optional_tag is None


def test_base_model_extra_fields_forbidden() -> None:
    """AC-1.2-01: Verify extra unknown fields are rejected strictly."""
    with pytest.raises(ValidationError) as exc_info:
        SampleModel.model_validate({"name": "test", "count": 1, "unknown_field": "injected"})
    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_base_model_immutability() -> None:
    """AC-1.2-01: Verify frozen model raises error on attribute assignment."""
    m = SampleModel(name="test", count=1)
    with pytest.raises(ValidationError):
        # Attribute assignment on frozen Pydantic model
        m.name = "mutated"  # type: ignore[misc]


def test_base_model_str_strip_whitespace() -> None:
    """Verify whitespace is trimmed from string fields automatically."""
    m = SampleModel(name="  padded_string  ", count=5)
    assert m.name == "padded_string"


def test_base_model_dict_and_json_methods() -> None:
    """Verify to_dict and to_json serialization helpers."""
    m = SampleModel(name="alpha", count=10, optional_tag="tag1")
    d = m.to_dict()
    assert d == {"name": "alpha", "count": 10, "optional_tag": "tag1"}
    j = m.to_json()
    assert '"name":"alpha"' in j
    assert '"count":10' in j
