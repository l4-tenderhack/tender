from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings


class ParserService:

    def __init__(self, db_session: AsyncSession, settings: Settings) -> None:
        self.db_session = db_session
        self.settings = settings

    async def create_parse_job(self, source: str) -> str:
        _ = source
        raise NotImplementedError("Parsing workflow is not implemented yet.")
