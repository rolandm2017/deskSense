# test_session.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional

from activitytracker.db.database import get_db
from activitytracker.db.test_schema_manager import test_schema_manager

router = APIRouter(prefix="/api/test", tags=["testing"])


class TestSessionRequest(BaseModel):
    input_file: str
    duration_min: int = 30
    test_name: str = "Activity Tracker Test"


class TestSessionResponse(BaseModel):
    success: bool
    message: str
    schema_name: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/prepare")
async def prepare_test_environment(
    request: TestSessionRequest, db: AsyncSession = Depends(get_db)
) -> TestSessionResponse:
    """Prepare the test environment by creating a new schema."""
    try:
        # Create a new test schema
        schema_name = await test_schema_manager.create_schema(
            test_name=request.test_name, input_file=request.input_file
        )

        # Generate a session ID (you could use the schema name or create another ID)
        session_id = schema_name.replace("test_", "session_")

        return TestSessionResponse(
            success=True,
            message=f"Test environment prepared successfully",
            schema_name=schema_name,
            session_id=session_id,
        )
    except Exception as e:
        return TestSessionResponse(
            success=False, message=f"Failed to prepare test environment: {str(e)}"
        )


@router.post("/start/{session_id}")
async def start_test_session(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> TestSessionResponse:
    """Start an existing test session."""
    # Convert session ID to schema name
    schema_name = session_id.replace("session_", "test_")

    # Set the current schema
    success = await test_schema_manager.set_schema(schema_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Test session {session_id} not found")

    # Update the schema status
    await test_schema_manager.mark_schema_status("RUNNING")

    return TestSessionResponse(
        success=True,
        message=f"Test session {session_id} started",
        schema_name=schema_name,
        session_id=session_id,
    )


@router.post("/end/{session_id}")
async def end_test_session(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> TestSessionResponse:
    """End a test session and mark it as completed."""
    # Convert session ID to schema name
    schema_name = session_id.replace("session_", "test_")

    # Set the schema to ensure we're ending the right one
    success = await test_schema_manager.set_schema(schema_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Test session {session_id} not found")

    # Mark the schema as completed
    await test_schema_manager.mark_schema_status("COMPLETED")

    # Reset the current schema
    test_schema_manager.current_schema = None

    return TestSessionResponse(
        success=True, message=f"Test session {session_id} ended", session_id=session_id
    )


@router.get("/sessions")
async def list_test_sessions(db: AsyncSession = Depends(get_db)):
    """List all test sessions."""
    test_schemas = await test_schema_manager.list_test_schemas()
    return {
        "sessions": [
            {
                "session_id": schema["schema_name"].replace("test_", "session_"),
                "schema": schema["schema_name"],
                "info": schema["info"],
            }
            for schema in test_schemas
        ]
    }


@router.delete("/sessions/{session_id}")
async def delete_test_session(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> TestSessionResponse:
    """Delete a test session and its schema."""
    # Convert session ID to schema name
    schema_name = session_id.replace("session_", "test_")

    # Drop the schema
    success = await test_schema_manager.drop_schema(schema_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Test session {session_id} not found")

    return TestSessionResponse(success=True, message=f"Test session {session_id} deleted")
