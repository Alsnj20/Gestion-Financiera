"""Unit tests for Category entity."""

import pytest

from modules.categories.domain.entities.category import Category
from shared.errors import ValidationError
from shared.types.enums import CategoryStatus, CategoryType


def test_create_category():
    cat = Category.create(
        user_id="user-123",
        name="Alimentación",
        type=CategoryType.EXPENSE,
    )
    assert cat.user_id == "user-123"
    assert cat.name == "Alimentación"
    assert cat.type == CategoryType.EXPENSE
    assert cat.status == CategoryStatus.ACTIVE
    assert cat.is_root is True


def test_create_category_with_parent():
    parent = Category.create(user_id="user-123", name="Comida")
    child = Category.create(
        user_id="user-123", name="Restaurantes", parent_id=parent.id
    )
    assert child.parent_id == parent.id
    assert child.is_root is False


def test_category_name_required():
    with pytest.raises(ValidationError) as exc_info:
        Category.create(user_id="user-123", name="")
    assert exc_info.value.code == "CAT_NAME_REQUIRED"


def test_category_user_required():
    with pytest.raises(ValidationError) as exc_info:
        Category.create(user_id="", name="Test")
    assert exc_info.value.code == "CAT_USER_REQUIRED"


def test_archive_category():
    cat = Category.create(user_id="user-123", name="Test")
    archived = cat.archive()
    assert archived.status == CategoryStatus.ARCHIVED


def test_create_category_with_visual():
    cat = Category.create(
        user_id="user-123",
        name="Comida",
        icon="IconShoppingCart",
        color="#F79009",
    )
    assert cat.icon == "IconShoppingCart"
    assert cat.color == "#F79009"


def test_change_visual():
    cat = Category.create(user_id="user-123", name="Comida")
    updated = cat.change_visual("IconCar", "#2E90FA")
    assert updated.icon == "IconCar"
    assert updated.color == "#2E90FA"


def test_icon_too_long():
    with pytest.raises(ValidationError) as exc_info:
        Category.create(user_id="user-123", name="Test", icon="x" * 41)
    assert exc_info.value.code == "CAT_ICON_TOO_LONG"
