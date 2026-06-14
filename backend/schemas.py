from pydantic import BaseModel
from datetime import datetime


class TagSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class TagWithCount(BaseModel):
    id: int
    name: str
    count: int


class ImageSchema(BaseModel):
    id: int
    filename: str
    url: str
    tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_image(cls, img) -> "ImageSchema":
        return cls(
            id=img.id,
            filename=img.filename,
            url=img.url,
            tags=[t.name for t in img.tags],
            created_at=img.created_at,
        )


class AddTagsRequest(BaseModel):
    tags: list[str]


class SyncResult(BaseModel):
    added: int
    total: int
