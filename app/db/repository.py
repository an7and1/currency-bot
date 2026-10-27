from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import History, User


async def get_or_create_user(session: AsyncSession, vk_id: int) -> User:
    result = await session.execute(select(User).where(User.vk_id == vk_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(vk_id=vk_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def set_favorite_pair(session: AsyncSession, vk_id: int, pair: str) -> None:
    user = await get_or_create_user(session, vk_id)
    user.favorite_pair = pair
    await session.commit()


async def get_favorite_pair(session: AsyncSession, vk_id: int) -> str | None:
    user = await get_or_create_user(session, vk_id)
    return user.favorite_pair


async def add_history(
    session: AsyncSession, vk_id: int, query: str, response: str
) -> None:
    user = await get_or_create_user(session, vk_id)
    session.add(History(user_id=user.id, query=query, response=response))
    await session.commit()


async def get_recent_history(
    session: AsyncSession, vk_id: int, limit: int = 5
) -> list[History]:
    user = await get_or_create_user(session, vk_id)
    result = await session.execute(
        select(History)
        .where(History.user_id == user.id)
        .order_by(desc(History.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())
