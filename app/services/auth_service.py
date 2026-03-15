from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.schemas.auth import TokenResponse, UserResponse


class AuthService:

    def __init__(self, db_session: AsyncSession, settings: Settings) -> None:
        self.db_session = db_session
        self.settings = settings

    async def login(self, username: str, password: str) -> TokenResponse:
        _ = username, password
        raise NotImplementedError("JWT authentication is not implemented yet.")

    async def get_current_user(self, token: str) -> UserResponse:
        _ = token
        raise NotImplementedError("JWT authentication is not implemented yet.")
