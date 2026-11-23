import asyncio

from app.database.mongo import get_database
from app.shared.auth.identity_repository import MongoIdentityRepository


async def main() -> None:
    database = get_database()
    repository = MongoIdentityRepository(
        users=database["identity_users"],
        consumers=database["identity_consumers"],
        refresh_tokens=database["identity_refresh_tokens"],
    )
    await repository.ensure_indexes()
    await database.client.close()


if __name__ == "__main__":
    asyncio.run(main())