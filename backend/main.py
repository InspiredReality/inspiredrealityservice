import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

from database import engine, get_db, Base
from schemas import ImageSchema, TagWithCount, AddTagsRequest, SyncResult
import crud
import github_sync

load_dotenv()


def require_admin(authorization: str | None = Header(default=None)):
    token = os.environ.get("ADMIN_TOKEN", "")
    if not token or authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Sticker API", lifespan=lifespan)

allowed_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@app.get("/stickers", response_model=dict)
async def list_stickers(
    tags: str | None = Query(default=None, description="Comma-separated tag names"),
    mode: str = Query(default="or", pattern="^(and|or)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    tag_list = [t for t in (tags or "").split(",") if t.strip()] if tags else []
    images, total = await crud.get_images(db, tag_list or None, mode, limit, offset)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [ImageSchema.from_orm_image(img) for img in images],
    }


@app.get("/stickers/random", response_model=ImageSchema | None)
async def random_sticker(
    tags: str | None = Query(default=None),
    mode: str = Query(default="or", pattern="^(and|or)$"),
    db: AsyncSession = Depends(get_db),
):
    tag_list = [t for t in (tags or "").split(",") if t.strip()] if tags else []
    image = await crud.get_random_image(db, tag_list or None, mode)
    if not image:
        raise HTTPException(status_code=404, detail="No matching stickers found")
    return ImageSchema.from_orm_image(image)


@app.get("/tags", response_model=list[TagWithCount])
async def list_tags(db: AsyncSession = Depends(get_db)):
    rows = await crud.get_all_tags_with_counts(db)
    return [TagWithCount(**r) for r in rows]


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    tag: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    images = await crud.get_all_images_for_admin(db, tag)
    all_tags = await crud.get_all_tags_with_counts(db)
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "images": images,
            "all_tags": all_tags,
            "filter_tag": tag or "",
        },
    )


@app.post("/admin/sync-images", response_model=SyncResult)
async def sync_images(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    result = await github_sync.sync_images_from_github(db)
    return SyncResult(**result)


@app.post("/admin/images/{image_id}/tags", response_model=ImageSchema)
async def add_tags(
    image_id: int,
    body: AddTagsRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    image = await crud.add_tags_to_image(db, image_id, body.tags)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return ImageSchema.from_orm_image(image)


@app.delete("/admin/images/{image_id}/tags/{tag_name}", status_code=204)
async def remove_tag(
    image_id: int,
    tag_name: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    removed = await crud.remove_tag_from_image(db, image_id, tag_name)
    if not removed:
        raise HTTPException(status_code=404, detail="Tag not found on image")
