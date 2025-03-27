# import pytest
# import asyncio
# from httpx import AsyncClient
# from collections import Counter


# from fastapi.testclient import TestClient
# from surveillance.server import app
# from surveillance.src.db.database import init_db

# ###
# ##
# # YOU MUST have the actual development server running
# # for these tests to work.
# ##
# ###


# @pytest.fixture(autouse=True)
# async def setup_db():
#     await init_db()


# @pytest.fixture
# def client():
#     return TestClient(app)


# @pytest.mark.asyncio
# async def test_health_check():
#     async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
#         response = await client.get("http://127.0.0.1:8000/health")
#         assert response.status_code == 200
#         body = response.json()
#         assert body["status"] == "healthy"


# @pytest.mark.asyncio
# async def test_timeline():
#     async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
#         response = await client.get("http://127.0.0.1:8000/dashboard/timeline")
#         assert response.status_code == 200

#         timeline_content = response.json()
#         assert timeline_content["mouseRows"] is not None
#         assert len(timeline_content["mouseRows"]) > 0
#         assert timeline_content["keyboardRows"] is not None
#         assert len(timeline_content["keyboardRows"]) > 0


# @pytest.mark.asyncio
# async def test_summaries():
#     async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
#         response = await client.get("http://127.0.0.1:8000/dashboard/program/summaries")
#         assert response.status_code == 200

#         summaries = response.json()
#         assert summaries["columns"] is not None
#         # assert len(summaries["columns"]) > 0  # Would do this but, sometimes it really is 0 on a functioning endpoint


# @pytest.mark.asyncio
# async def test_timeline_contains_no_duplicates():
#     async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
#         response = await client.get("http://127.0.0.1:8000/dashboard/timeline")

#         timeline_content = response.json()
#         mouse_rows = timeline_content["mouseRows"]
#         keyboard_rows = timeline_content["keyboardRows"]

#         # Check for duplicate values in "id"
#         # Check for duplicate values in "group"
#         # Check for duplicate values in "content"
#         #
#         # ### Keyboard
#         ids = [row["id"] for row in keyboard_rows]
#         id_counts = Counter(ids)

#         content = [row["content"] for row in keyboard_rows]
#         content_counts = Counter(content)

#         # ### do some checking
#         single_ids = [id for id, count in id_counts.items() if count == 1]
#         duplicate_ids = [id for id, count in id_counts.items() if count > 1]
#         single_groups = [group for group,
#                          count in content_counts.items() if count == 1]
#         duplicate_groups = [group for group,
#                             count in content_counts.items() if count > 1]

#         assert len(duplicate_ids) == 0
#         assert len(single_ids) == len(keyboard_rows)
#         assert len(duplicate_groups) == 0
#         assert len(single_groups) == len(keyboard_rows)

#         # Continue with keyboard checking
#         assert all(count == 1 for count in id_counts.values())
#         assert all(count == 1 for count in content_counts.values())

#         # ### Mouse
#         ids = [row["id"] for row in mouse_rows]
#         id_counts = Counter(ids)
#         content = [row["content"] for row in mouse_rows]
#         content_counts = Counter(content)

#         assert all(count == 1 for count in id_counts.values())
#         assert all(count == 1 for count in content_counts.values())

# # FIXME: HoursSpent on DailySummary table is suspiciously low
