"""Unit tests for Categories/Tags/Budgets/Limits (fakes, no DB)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from modules.budgets.application.use_cases.archive_budget import (
    ArchiveBudgetInput,
)
from modules.budgets.application.use_cases.create_budget import (
    CreateBudgetInput,
    CreateBudgetUseCase,
)
from modules.budgets.application.use_cases.update_budget import UpdateBudgetInput
from modules.budgets.domain.entities.budget import Budget
from modules.budgets.presentation.controllers.budget_controller import BudgetController
from modules.categories.application.use_cases.archive_category import (
    ArchiveCategoryInput,
    ArchiveCategoryUseCase,
)
from modules.categories.application.use_cases.create_category import (
    CreateCategoryInput,
    CreateCategoryUseCase,
)
from modules.categories.application.use_cases.restore_category import (
    RestoreCategoryInput,
    RestoreCategoryUseCase,
)
from modules.categories.application.use_cases.update_category import (
    UpdateCategoryInput,
    UpdateCategoryUseCase,
)
from modules.categories.domain.entities.category import Category
from modules.limits.application.use_cases.archive_limit import (
    ArchiveLimitInput,
    ArchiveLimitUseCase,
)
from modules.limits.application.use_cases.create_limit import (
    CreateLimitInput,
)
from modules.limits.domain.entities.limit import Limit
from modules.limits.presentation.controllers.limit_controller import LimitController
from modules.tags.application.use_cases.create_tag import (
    CreateTagInput,
)
from modules.tags.application.use_cases.delete_tag import (
    DeleteTagInput,
    DeleteTagUseCase,
)
from modules.tags.application.use_cases.update_tag import (
    UpdateTagInput,
    UpdateTagUseCase,
)
from modules.tags.domain.entities.tag import Tag
from modules.tags.presentation.controllers.tag_controller import TagController
from shared.errors import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from shared.types.enums import CategoryStatus


class FakeCategoryRepo:
    def __init__(self, items: list[Category] | None = None) -> None:
        self.store: dict[str, Category] = {c.id: c for c in (items or [])}

    async def save(self, category: Category) -> None:
        self.store[category.id] = category

    async def find_by_id(self, category_id: str, **kwargs) -> Category | None:
        return self.store.get(category_id)

    async def find_by_user(self, user_id: str) -> list[Category]:
        return [c for c in self.store.values() if c.user_id == user_id]

    async def exists_name_for_user(
        self, user_id: str, name: str, parent_id: str = ""
    ) -> bool:
        return any(
            c
            for c in self.store.values()
            if c.user_id == user_id
            and c.name == name.strip()
            and c.parent_id == parent_id
        )


class FakeTagRepo:
    def __init__(self, items: list[Tag] | None = None) -> None:
        self.store: dict[str, Tag] = {t.id: t for t in (items or [])}

    async def save(self, tag: Tag) -> None:
        self.store[tag.id] = tag

    async def find_by_id(self, tag_id: str, **kwargs) -> Tag | None:
        return self.store.get(tag_id)

    async def find_by_user(self, user_id: str) -> list[Tag]:
        return [t for t in self.store.values() if t.user_id == user_id]

    async def exists_name_for_user(self, user_id: str, name: str) -> bool:
        from modules.tags.domain.entities.tag import normalize_tag_name

        normalized = normalize_tag_name(name)
        return any(
            t
            for t in self.store.values()
            if t.user_id == user_id and t.name == normalized
        )

    async def delete(self, tag_id: str) -> None:
        self.store.pop(tag_id, None)


class FakeBudgetRepo:
    def __init__(self, items: list[Budget] | None = None) -> None:
        self.store: dict[str, Budget] = {b.id: b for b in (items or [])}

    async def save(self, budget: Budget) -> None:
        self.store[budget.id] = budget

    async def find_by_id(self, budget_id: str, **kwargs) -> Budget | None:
        return self.store.get(budget_id)

    async def find_by_user(self, user_id: str) -> list[Budget]:
        return [b for b in self.store.values() if b.user_id == user_id]


class FakeLimitRepo:
    def __init__(self, items: list[Limit] | None = None) -> None:
        self.store: dict[str, Limit] = {l.id: l for l in (items or [])}

    async def save(self, limit: Limit) -> None:
        self.store[limit.id] = limit

    async def find_by_id(self, limit_id: str, **kwargs) -> Limit | None:
        return self.store.get(limit_id)

    async def find_by_user(self, user_id: str) -> list[Limit]:
        return [l for l in self.store.values() if l.user_id == user_id]


class FakeSession:
    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


def _cat(**kwargs) -> Category:
    base = {"user_id": "user-1", "name": "Mercado"}
    base.update(kwargs)
    return Category.create(**base)


# ---------- categories: jerarquía ----------


async def test_category_rejects_foreign_parent():
    mine = FakeCategoryRepo()
    theirs = FakeCategoryRepo([Category.create(user_id="other", name="X")])
    parent = next(iter(theirs.store.values()))

    class Combined:
        async def save(self, c):
            await mine.save(c)

        async def find_by_id(self, i, **k):
            return (await mine.find_by_id(i)) or (await theirs.find_by_id(i))

        async def find_by_user(self, u):
            return await mine.find_by_user(u)

        async def exists_name_for_user(self, u, n, p=""):
            return await mine.exists_name_for_user(u, n, p)

    with pytest.raises(BusinessRuleError) as exc:
        await CreateCategoryUseCase(Combined()).execute(
            CreateCategoryInput(user_id="user-1", name="Hija", parent_id=parent.id)
        )
    assert exc.value.code == "FORBIDDEN"


async def test_category_rejects_cycle():
    repo = FakeCategoryRepo()
    parent = _cat(name="Padre")
    child = Category.create(user_id="user-1", name="Hija", parent_id=parent.id)
    repo.store[parent.id] = parent
    repo.store[child.id] = child
    # Padre bajo su propia hija = ciclo A->B->A.
    with pytest.raises(BusinessRuleError) as exc:
        await UpdateCategoryUseCase(repo).execute(
            UpdateCategoryInput(
                category_id=parent.id, user_id="user-1", parent_id=child.id
            )
        )
    assert exc.value.code == "CAT_CYCLE"


async def test_category_archive_frees_name_and_restore():
    repo = FakeCategoryRepo([_cat(name="Mercado")])
    cat = next(iter(repo.store.values()))
    await ArchiveCategoryUseCase(repo).execute(
        ArchiveCategoryInput(category_id=cat.id, user_id="user-1")
    )
    saved = repo.store[cat.id]
    assert saved.status == CategoryStatus.ARCHIVED
    assert saved.name.startswith("Mercado_deleted_")
    assert not await repo.exists_name_for_user("user-1", "Mercado", "")

    out = await RestoreCategoryUseCase(repo).execute(
        RestoreCategoryInput(category_id=cat.id, user_id="user-1")
    )
    assert out.name == "Mercado"
    assert out.status == "ACTIVE"


async def test_category_archived_cannot_update():
    repo = FakeCategoryRepo([_cat(name="Vieja").archive_with_shadow_name()])
    cat = next(iter(repo.store.values()))
    with pytest.raises(BusinessRuleError) as exc:
        await UpdateCategoryUseCase(repo).execute(
            UpdateCategoryInput(category_id=cat.id, user_id="user-1", name="X")
        )
    assert exc.value.code == "CAT_ARCHIVED"


# ---------- tags ----------


async def test_tag_update_preserves_lowercase_invariant():
    repo = FakeTagRepo([Tag.create(user_id="user-1", name="urgente")])
    tag = next(iter(repo.store.values()))
    out = await UpdateTagUseCase(repo).execute(
        UpdateTagInput(tag_id=tag.id, user_id="user-1", name="#URGENTE")
    )
    assert out.name == "urgente"  # normalizado, sin duplicado


async def test_tag_delete_is_physical():
    repo = FakeTagRepo([Tag.create(user_id="user-1", name="x")])
    tag = next(iter(repo.store.values()))
    await DeleteTagUseCase(repo).execute(
        DeleteTagInput(tag_id=tag.id, user_id="user-1")
    )
    assert tag.id not in repo.store


async def test_tag_controller_conflict_409():
    repo = FakeTagRepo([Tag.create(user_id="user-1", name="a")])
    controller = TagController(repo, FakeSession())
    with pytest.raises(HTTPException) as exc:
        await controller.create(CreateTagInput(user_id="user-1", name="A"))
    assert exc.value.status_code == 409


# ---------- budgets ----------


def _budget(**kwargs) -> Budget:
    base = {
        "user_id": "user-1",
        "name": "Mensual",
        "amount": Decimal("1000.00"),
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 1, 31),
    }
    base.update(kwargs)
    return Budget.create(**base)


async def test_budget_rejects_inverted_period():
    with pytest.raises(ValidationError) as exc:
        _budget(period_start=date(2026, 2, 1), period_end=date(2026, 1, 1))
    assert exc.value.code == "BUDGET_PERIOD_INVALID"


async def test_budget_rejects_unknown_category():
    repo = FakeBudgetRepo()
    with pytest.raises(NotFoundError):
        await CreateBudgetUseCase(repo, FakeCategoryRepo()).execute(
            CreateBudgetInput(
                user_id="user-1",
                name="B",
                amount=Decimal("10.00"),
                period_start=date(2026, 1, 1),
                period_end=date(2026, 1, 31),
                category_id="missing",
            )
        )


async def test_budget_archive_restore_flow():
    repo = FakeBudgetRepo([_budget()])
    budget = next(iter(repo.store.values()))
    controller = BudgetController(repo, FakeCategoryRepo(), FakeSession())
    await controller.archive(ArchiveBudgetInput(budget_id=budget.id, user_id="user-1"))
    assert repo.store[budget.id].status.value == "ARCHIVED"
    with pytest.raises(HTTPException) as exc:
        await controller.update(
            UpdateBudgetInput(budget_id=budget.id, user_id="user-1", name="X")
        )
    assert exc.value.detail["code"] == "BUDGET_ARCHIVED"


# ---------- limits ----------


async def test_limit_rejects_out_of_range_threshold():
    from modules.limits.domain.entities.limit import Limit as LimitEntity

    with pytest.raises(ValidationError) as exc:
        LimitEntity.create(
            user_id="user-1",
            name="L",
            amount=Decimal("100.00"),
            threshold_warning=Decimal(150),
        )
    assert exc.value.code == "LIMIT_THRESHOLD_OUT_OF_RANGE"


async def test_limit_create_and_archive():
    repo = FakeLimitRepo()
    controller = LimitController(repo, FakeCategoryRepo(), FakeSession())
    out = await controller.create(
        CreateLimitInput(user_id="user-1", name="L", amount=Decimal("500.00"))
    )
    assert out["status"] == "ACTIVE"
    await ArchiveLimitUseCase(repo).execute(
        ArchiveLimitInput(limit_id=out["id"], user_id="user-1")
    )
    assert repo.store[out["id"]].status.value == "ARCHIVED"
