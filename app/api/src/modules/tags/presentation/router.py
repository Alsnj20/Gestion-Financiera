"""Tag Router — Solo enruta, delega al Controller."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from composition import get_tag_controller
from modules.auth.presentation.dependencies import get_current_user, require_active_user
from modules.tags.application.use_cases.create_tag import CreateTagInput
from modules.tags.application.use_cases.delete_tag import DeleteTagInput
from modules.tags.application.use_cases.get_tag import GetTagInput
from modules.tags.application.use_cases.list_tags import ListTagsInput
from modules.tags.application.use_cases.update_tag import UpdateTagInput
from modules.tags.presentation.controllers.tag_controller import TagController
from modules.tags.presentation.schemas import (
    CreateTagRequestSchema,
    TagResponseSchema,
    UpdateTagRequestSchema,
)

router = APIRouter(prefix="/tags", tags=["tags"])

CurrentUser = Annotated[dict, Depends(get_current_user)]
ActiveUser = Annotated[dict, Depends(require_active_user)]
TagCtrl = Annotated[TagController, Depends(get_tag_controller)]


@router.post("", response_model=TagResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: CreateTagRequestSchema,
    current_user: CurrentUser,
    controller: TagCtrl,
):
    # user_id sale del JWT, nunca del body.
    result = await controller.create(
        CreateTagInput(user_id=current_user["user_id"], name=payload.name)
    )
    return TagResponseSchema(**result)


@router.get("/user/{user_id}", response_model=list[TagResponseSchema])
async def list_tags_by_user(
    user_id: str,
    current_user: CurrentUser,
    controller: TagCtrl,
):
    result = await controller.list_by_user(
        ListTagsInput(
            user_id=user_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return [TagResponseSchema(**item) for item in result]


@router.get("/{tag_id}", response_model=TagResponseSchema)
async def get_tag(
    tag_id: str,
    current_user: CurrentUser,
    controller: TagCtrl,
):
    result = await controller.get(
        GetTagInput(
            tag_id=tag_id,
            requester_id=current_user["user_id"],
            requester_role=current_user.get("role", "USER"),
        )
    )
    return TagResponseSchema(**result)


@router.put("/{tag_id}", response_model=TagResponseSchema)
async def update_tag(
    tag_id: str,
    payload: UpdateTagRequestSchema,
    current_user: ActiveUser,
    controller: TagCtrl,
):
    result = await controller.update(
        UpdateTagInput(
            tag_id=tag_id,
            user_id=current_user["user_id"],
            name=payload.name,
        )
    )
    return TagResponseSchema(**result)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    current_user: ActiveUser,
    controller: TagCtrl,
):
    """Borrado físico: tags sin historial; asociaciones caen en cascada."""
    await controller.delete(
        DeleteTagInput(tag_id=tag_id, user_id=current_user["user_id"])
    )
