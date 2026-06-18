import pytest
from app.models.user import User
from app.schemas.user import UserCreate
from app.services import user_service
from unittest.mock import patch

def test_create_user_transaction_rollback(db_session):
    user_in = UserCreate(email="transaction@example.com", password="password123")
    
    # We patch Organization to raise an exception when initialized
    with patch("app.services.user_service.Organization", side_effect=Exception("Mocked DB Failure")):
        with pytest.raises(Exception, match="Mocked DB Failure"):
            user_service.create_user(db_session, user_in=user_in)
    
    # Assert that the user was NOT saved (rollback occurred)
    user = db_session.query(User).filter(User.email == "transaction@example.com").first()
    assert user is None
