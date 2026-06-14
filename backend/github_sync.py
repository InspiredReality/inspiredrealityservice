import os
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from crud import upsert_image


async def sync_images_from_github(db: AsyncSession) -> dict:
    repo = os.environ["GITHUB_REPO"]
    branch = os.environ.get("GITHUB_BRANCH", "main")
    jsdelivr_base = os.environ["JSDELIVR_BASE"].rstrip("/") + "/"
    github_token = os.environ.get("GITHUB_TOKEN")

    url = f"https://api.github.com/repos/{repo}/contents/images?ref={branch}"
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        contents = response.json()

    added = 0
    total = 0
    for item in contents:
        if item["type"] != "file":
            continue
        filename = item["name"]
        if not filename.lower().endswith(".png"):
            continue
        total += 1
        cdn_url = jsdelivr_base + filename
        _, is_new = await upsert_image(db, filename, cdn_url)
        if is_new:
            added += 1

    await db.commit()
    return {"added": added, "total": total}
