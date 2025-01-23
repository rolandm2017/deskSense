# import pytest
# import pytest_asyncio
# from fastapi.testclient import TestClient
# from httpx import AsyncClient
# import asyncio
# from collections import Counter

# from surveillance.server import app, SurveillanceState
# from surveillance.src.surveillance_manager import SurveillanceManager
# from surveillance.src.db.database import init_db, async_session_maker

# # First create an event loop fixture

# test_app = TestClient(app=app)


# @pytest.fixture(scope="session")
# def event_loop():
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()

# # Then handle the lifespan


# @pytest.fixture(scope="session")
# async def initialized_app():
#     async with app.router.lifespan.enter_async_context():
#         await init_db()  # Make sure DB is initialized
#         yield app

# # Finally create the test client


# @pytest.fixture(scope="session")
# async def test_client(initialized_app):
#     async with AsyncClient(app=initialized_app, base_url="http://test") as client:
#         yield client


# # @pytest.mark.asyncio
# @pytest_asyncio.fixture()
# async def test_health_check(test_client):
#     await init_db()

#     # Use the session_maker directly
#     surveillance_state = SurveillanceState()

#     surveillance_state.manager = SurveillanceManager(async_session_maker)
#     surveillance_state.manager.start_trackers()
#     test_app.surve
#     response = test_app.get("/health")
#     if response.status_code != 200:
#         print("Response content:", response.json())
#     assert response.status_code == 200
#     assert response.json()["status"] == "healthy"


# # @pytest.mark.asyncio
# @pytest_asyncio.fixture()
# async def test_timeline(test_client):
#     response = test_client.get("/dashboard/timeline")
#     print(response, '32ru')
#     assert response.status_code == 200

#     timeline_content = response.json()
#     print(timeline_content, '35ru')
#     assert timeline_content["mouseRows"] is not None
#     assert len(timeline_content["mouseRows"]) > 0
#     assert timeline_content["keyboardRows"] is not None
#     assert len(timeline_content["keyboardRows"]) > 0


# @pytest.mark.asyncio
# async def test_summaries(test_client):
#     async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
#         response = await client.get("http://127.0.0.1:8000/dashboard/summaries")
#         assert response.status_code == 200

#         summaries = response.json()
#         assert summaries["columns"] is not None
#         assert len(summaries["columns"]) > 0


# # @pytest.mark.asyncio
# # async def test_timeline_contains_no_duplicates():
# #     async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
# #         response = await client.get("http://127.0.0.1:8000/dashboard/timeline")

# #         timeline_content = response.json()
# #         # print(timeline_content, '35ru')
# #         mouse_rows = timeline_content["mouseRows"]
# #         keyboard_rows = timeline_content["keyboardRows"]

# #         # Check for duplicate values in "id"
# #         # Check for duplicate values in "group"
# #         # Check for duplicate values in "content"
# #         #
# #         # ### Keyboard
# #         ids = [row["id"] for row in keyboard_rows]
# #         id_counts = Counter(ids)
# #         groups = [row["group"] for row in keyboard_rows]
# #         group_counts = Counter(groups)

# #         assert all(count == 1 for count in id_counts.values())
# #         assert all(count == 1 for count in group_counts.values())

# #         # ### Mouse
# #         ids = [row["id"] for row in mouse_rows]
# #         id_counts = Counter(ids)
# #         groups = [row["group"] for row in mouse_rows]
# #         group_counts = Counter(groups)

# #         assert all(count == 1 for count in id_counts.values())
# #         assert all(count == 1 for count in group_counts.values())

# # FIXME: HoursSpent on DailySummary table is suspiciously low
