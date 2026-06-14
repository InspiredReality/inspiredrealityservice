from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
import random

from models import Image, Tag, image_tags


async def get_or_create_tag(db: AsyncSession, name: str) -> Tag:
    name = name.strip().lower()
    result = await db.execute(select(Tag).where(Tag.name == name))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=name)
        db.add(tag)
        await db.flush()
    return tag


async def get_all_tags_with_counts(db: AsyncSession) -> list[dict]:
    stmt = (
        select(Tag.id, Tag.name, func.count(image_tags.c.image_id).label("count"))
        .outerjoin(image_tags, Tag.id == image_tags.c.tag_id)
        .group_by(Tag.id, Tag.name)
        .order_by(Tag.name)
    )
    result = await db.execute(stmt)
    return [{"id": r.id, "name": r.name, "count": r.count} for r in result]


def _build_tag_filter_query(tags: list[str], mode: str):
    """Return a subquery of image IDs matching the tag filter."""
    tag_names = [t.strip().lower() for t in tags if t.strip()]
    if not tag_names:
        return None, False

    if mode == "and":
        # Images that have ALL requested tags
        subq = (
            select(image_tags.c.image_id)
            .join(Tag, Tag.id == image_tags.c.tag_id)
            .where(Tag.name.in_(tag_names))
            .group_by(image_tags.c.image_id)
            .having(func.count(func.distinct(Tag.name)) == len(tag_names))
            .subquery()
        )
    else:
        # Images that have ANY of the requested tags (OR)
        subq = (
            select(image_tags.c.image_id)
            .join(Tag, Tag.id == image_tags.c.tag_id)
            .where(Tag.name.in_(tag_names))
            .distinct()
            .subquery()
        )
    return subq, True


async def get_images(
    db: AsyncSession,
    tags: list[str] | None,
    mode: str = "or",
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Image], int]:
    stmt = select(Image).options(selectinload(Image.tags))
    count_stmt = select(func.count()).select_from(Image)

    if tags:
        subq, has_filter = _build_tag_filter_query(tags, mode)
        if has_filter:
            stmt = stmt.where(Image.id.in_(subq))
            count_stmt = count_stmt.where(Image.id.in_(subq))

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(stmt.order_by(Image.id).limit(limit).offset(offset))
    images = result.scalars().all()
    return images, total


async def get_random_image(
    db: AsyncSession,
    tags: list[str] | None,
    mode: str = "or",
) -> Image | None:
    stmt = select(Image.id).options(selectinload(Image.tags))

    if tags:
        subq, has_filter = _build_tag_filter_query(tags, mode)
        if has_filter:
            stmt = stmt.where(Image.id.in_(subq))

    result = await db.execute(stmt)
    ids = result.scalars().all()
    if not ids:
        return None

    chosen_id = random.choice(ids)
    img_result = await db.execute(
        select(Image).options(selectinload(Image.tags)).where(Image.id == chosen_id)
    )
    return img_result.scalar_one_or_none()


async def add_tags_to_image(db: AsyncSession, image_id: int, tag_names: list[str]) -> Image | None:
    result = await db.execute(
        select(Image).options(selectinload(Image.tags)).where(Image.id == image_id)
    )
    image = result.scalar_one_or_none()
    if not image:
        return None

    existing = {t.name for t in image.tags}
    for name in tag_names:
        name = name.strip().lower()
        if name and name not in existing:
            tag = await get_or_create_tag(db, name)
            image.tags.append(tag)

    await db.commit()
    await db.refresh(image)
    return image


async def remove_tag_from_image(db: AsyncSession, image_id: int, tag_name: str) -> bool:
    tag_name = tag_name.strip().lower()
    result = await db.execute(select(Tag).where(Tag.name == tag_name))
    tag = result.scalar_one_or_none()
    if not tag:
        return False

    await db.execute(
        delete(image_tags).where(
            image_tags.c.image_id == image_id,
            image_tags.c.tag_id == tag.id,
        )
    )
    await db.commit()
    return True


async def upsert_image(db: AsyncSession, filename: str, url: str) -> tuple[Image, bool]:
    result = await db.execute(select(Image).where(Image.filename == filename))
    existing = result.scalar_one_or_none()
    if existing:
        return existing, False
    img = Image(filename=filename, url=url)
    db.add(img)
    await db.flush()
    return img, True


async def get_all_images_for_admin(db: AsyncSession, tag_filter: str | None = None) -> list[Image]:
    stmt = select(Image).options(selectinload(Image.tags))
    if tag_filter:
        tags = [t.strip().lower() for t in tag_filter.split(",") if t.strip()]
        if tags:
            subq, _ = _build_tag_filter_query(tags, "or")
            stmt = stmt.where(Image.id.in_(subq))

    result = await db.execute(stmt)
    images = result.scalars().all()
    # Untagged first, then by filename
    return sorted(images, key=lambda img: (len(img.tags) > 0, img.filename))
