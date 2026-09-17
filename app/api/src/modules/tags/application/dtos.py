"""DTOs de salida unificados del módulo tags.

Fuente única: `TagOutput` + `to_tag_output`.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.tags.domain.entities.tag import Tag


@dataclass(frozen=True, slots=True)
class TagOutput:
    id: str
    user_id: str
    name: str


def to_tag_output(tag: Tag) -> TagOutput:
    return TagOutput(id=tag.id, user_id=tag.user_id, name=tag.name)


# Aliases de compatibilidad.
CreateTagOutput = TagOutput
GetTagOutput = TagOutput
ListTagsOutput = TagOutput
UpdateTagOutput = TagOutput
