import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from src.api.dependencies import get_current_user, require_admin
from src.models.user import User, UserRole
import uuid


@pytest.mark.asyncio
async def test_get_current_user_with_existing_user():
    """Test get_current_user with existing user returns user."""
    # Create mock database session
    mock_db = MagicMock()

    # Create mock user
    mock_user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        firebase_uid="test-uid-123",
        email="test@example.com",
        name="Test User",
        role=UserRole.MEMBER
    )

    # Setup query mock chain
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = mock_user
    mock_query.filter.return_value = mock_filter
    mock_db.query.return_value = mock_query

    # Mock token data
    mock_token_data = {
        "uid": "test-uid-123",
        "email": "test@example.com"
    }

    # Call the function
    result = await get_current_user(db=mock_db, token_data=mock_token_data)

    # Assert
    assert result == mock_user
    mock_db.query.assert_called_once_with(User)


@pytest.mark.asyncio
async def test_get_current_user_with_nonexistent_user():
    """Test get_current_user with non-existent user raises 404."""
    # Create mock database session
    mock_db = MagicMock()

    # Setup query mock chain to return None
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = None
    mock_query.filter.return_value = mock_filter
    mock_db.query.return_value = mock_query

    # Mock token data
    mock_token_data = {
        "uid": "nonexistent-uid",
        "email": "nonexistent@example.com"
    }

    # Call the function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db=mock_db, token_data=mock_token_data)

    # Assert
    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_require_admin_with_admin_user():
    """Test require_admin with admin user returns user."""
    # Create mock admin user
    mock_admin = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        firebase_uid="admin-uid-123",
        email="admin@example.com",
        name="Admin User",
        role=UserRole.ADMIN
    )

    # Call the function
    result = await require_admin(current_user=mock_admin)

    # Assert
    assert result == mock_admin


@pytest.mark.asyncio
async def test_require_admin_with_non_admin_user():
    """Test require_admin with non-admin user raises 403."""
    # Create mock non-admin user
    mock_user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        firebase_uid="user-uid-123",
        email="user@example.com",
        name="Regular User",
        role=UserRole.MEMBER
    )

    # Call the function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(current_user=mock_user)

    # Assert
    assert exc_info.value.status_code == 403
    assert "Admin access required" in str(exc_info.value.detail)
