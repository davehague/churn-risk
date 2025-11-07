import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from src.core.auth import verify_firebase_token


@pytest.mark.asyncio
async def test_verify_valid_token():
    """Test verifying a valid Firebase token."""
    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid-token"
    )

    with patch("src.core.auth.auth.verify_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": "test-uid-123",
            "email": "test@example.com"
        }

        result = await verify_firebase_token(mock_credentials)

        assert result["uid"] == "test-uid-123"
        assert result["email"] == "test@example.com"
        mock_verify.assert_called_once_with("valid-token")


@pytest.mark.asyncio
async def test_verify_invalid_token():
    """Test verifying an invalid Firebase token."""
    from firebase_admin import auth as firebase_auth

    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-token"
    )

    with patch("src.core.auth.auth.verify_id_token") as mock_verify:
        mock_verify.side_effect = firebase_auth.InvalidIdTokenError("Invalid token")

        with pytest.raises(HTTPException) as exc_info:
            await verify_firebase_token(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_verify_expired_token():
    """Test verifying an expired Firebase token."""
    from firebase_admin import auth as firebase_auth

    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="expired-token"
    )

    with patch("src.core.auth.auth.verify_id_token") as mock_verify:
        # ExpiredIdTokenError requires a message and cause parameter
        mock_verify.side_effect = firebase_auth.ExpiredIdTokenError("Token expired", cause=None)

        with pytest.raises(HTTPException) as exc_info:
            await verify_firebase_token(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_verify_token_generic_error():
    """Test verifying a token with generic error."""
    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="error-token"
    )

    with patch("src.core.auth.auth.verify_id_token") as mock_verify:
        mock_verify.side_effect = Exception("Unknown error")

        with pytest.raises(HTTPException) as exc_info:
            await verify_firebase_token(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Authentication failed" in str(exc_info.value.detail)
