import pytest
import asyncio
from httpx import AsyncClient
from collections import Counter


from fastapi.testclient import TestClient
from surveillance.server import app
from surveillance.src.db.database import init_db


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
        print(client, '25ru')
        response = await client.get("http://127.0.0.1:8000/health")
        print(response, '27ru')

        assert response.json()["status"] == "healthy"
        assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.skip(reason="passing for isolation")
async def test_timeline():
    async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.get("http://127.0.0.1:8000/dashboard/timeline")
        print(response, '32ru')
        assert response.status_code == 200

        timeline_content = response.json()
        print(timeline_content, '35ru')
        assert timeline_content["mouseRows"] is not None
        assert len(timeline_content["mouseRows"]) > 0
        assert timeline_content["keyboardRows"] is not None
        assert len(timeline_content["keyboardRows"]) > 0


@pytest.mark.asyncio
@pytest.mark.skip(reason="passing for isolation")
async def test_summaries():
    async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.get("http://127.0.0.1:8000/dashboard/summaries")
        assert response.status_code == 200

        summaries = response.json()
        assert summaries["columns"] is not None
        assert len(summaries["columns"]) > 0


# @pytest.mark.asyncio
# async def test_timeline_contains_no_duplicates():
#     async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
#         response = await client.get("http://127.0.0.1:8000/dashboard/timeline")

#         timeline_content = response.json()
#         # print(timeline_content, '35ru')
#         mouse_rows = timeline_content["mouseRows"]
#         keyboard_rows = timeline_content["keyboardRows"]

#         # Check for duplicate values in "id"
#         # Check for duplicate values in "group"
#         # Check for duplicate values in "content"
#         #
#         # ### Keyboard
#         ids = [row["id"] for row in keyboard_rows]
#         id_counts = Counter(ids)
#         groups = [row["group"] for row in keyboard_rows]
#         group_counts = Counter(groups)

#         assert all(count == 1 for count in id_counts.values())
#         assert all(count == 1 for count in group_counts.values())

#         # ### Mouse
#         ids = [row["id"] for row in mouse_rows]
#         id_counts = Counter(ids)
#         groups = [row["group"] for row in mouse_rows]
#         group_counts = Counter(groups)

#         assert all(count == 1 for count in id_counts.values())
#         assert all(count == 1 for count in group_counts.values())

# FIXME: HoursSpent on DailySummary table is suspiciously low
