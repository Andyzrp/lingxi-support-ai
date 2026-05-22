# backend/app/crud/channel.py
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Optional, List

from app.models.channel import Channel
from app.schemas.channel import ChannelCreate, ChannelUpdate


class CRUDChannel:
    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    async def create(
        self,
        db: AsyncSession,
        obj_in: ChannelCreate,
    ) -> Channel:
        db_obj = Channel(
            name=obj_in.name,
            type=int(obj_in.channel_type),  # ✅ channel_type → type
            channel_token=self._generate_token(),
            agent_id=obj_in.agent_id,
            description=obj_in.description,
            status=1,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(
        self,
        db: AsyncSession,
        channel_id: int,
    ) -> Optional[Channel]:
        result = await db.execute(select(Channel).where(Channel.id == channel_id))
        return result.scalar_one_or_none()

    async def get_by_token(
        self,
        db: AsyncSession,
        token: str,
    ) -> Optional[Channel]:
        result = await db.execute(select(Channel).where(Channel.channel_token == token))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
    ) -> List[Channel]:
        result = await db.execute(select(Channel).order_by(Channel.created_at.desc()))
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        channel_id: int,
        obj_in: ChannelUpdate,
    ) -> Optional[Channel]:
        update_data = {}
        if obj_in.name is not None:
            update_data["name"] = obj_in.name
        if obj_in.agent_id is not None:
            update_data["agent_id"] = obj_in.agent_id
        if obj_in.description is not None:
            update_data["description"] = obj_in.description
        if obj_in.status is not None:
            update_data["status"] = int(obj_in.status)

        if not update_data:
            return await self.get(db, channel_id)

        await db.execute(
            update(Channel).where(Channel.id == channel_id).values(**update_data)
        )
        await db.commit()
        return await self.get(db, channel_id)

    async def regenerate_token(
        self,
        db: AsyncSession,
        channel_id: int,
    ) -> Optional[Channel]:
        new_token = self._generate_token()
        await db.execute(
            update(Channel)
            .where(Channel.id == channel_id)
            .values(channel_token=new_token)
        )
        await db.commit()
        return await self.get(db, channel_id)

    async def get_by_agent(
        self,
        db: AsyncSession,
        agent_id: int,
    ) -> List[Channel]:
        result = await db.execute(select(Channel).where(Channel.agent_id == agent_id))
        return list(result.scalars().all())

    async def delete(self, db: AsyncSession, channel_id: int) -> bool:
        from app.models.channel import ChannelConfig

        await db.execute(
            delete(ChannelConfig).where(ChannelConfig.channel_id == channel_id)
        )
        result = await db.execute(delete(Channel).where(Channel.id == channel_id))
        await db.commit()
        return result.rowcount > 0


crud_channel = CRUDChannel()
