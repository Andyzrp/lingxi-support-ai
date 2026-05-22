# backend/app/crud/channel_config.py
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional, List

from app.models.channel import ChannelConfig


class CRUDChannelConfig:
    async def get_by_channel(
        self,
        db: AsyncSession,
        channel_id: int,
    ) -> List[ChannelConfig]:
        result = await db.execute(
            select(ChannelConfig)
            .where(ChannelConfig.channel_id == channel_id)
            .order_by(ChannelConfig.sort_order)
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        db: AsyncSession,
        channel_id: int,
        config_type: str,
        items: List[dict],
    ) -> List[ChannelConfig]:
        await db.execute(
            delete(ChannelConfig).where(
                ChannelConfig.channel_id == channel_id,
                ChannelConfig.config_type == config_type,
            )
        )

        objs = []
        for i, item in enumerate(items):
            title = item.get("title") or item.get("text") or item.get("label", "")
            content = item.get("content") or item.get("send_text", "")

            # subtitle/icon 等扩展字段统一存 extra
            extra_fields = {}
            if item.get("subtitle"):
                extra_fields["subtitle"] = item["subtitle"]
            if item.get("icon"):
                extra_fields["icon"] = item["icon"]
            extra = json.dumps(extra_fields) if extra_fields else None

            obj = ChannelConfig(
                channel_id=channel_id,
                config_type=config_type,
                title=title,
                content=content,
                image_url=item.get("image_url"),
                link_url=item.get("link_url"),
                icon=item.get("icon"),
                sort_order=item.get("sort_order") or i,
                status=item.get("status", 1),
                extra=extra,
            )
            objs.append(obj)

        db.add_all(objs)
        await db.commit()
        return objs

    async def delete_by_channel(
        self,
        db: AsyncSession,
        channel_id: int,
    ) -> None:
        await db.execute(
            delete(ChannelConfig).where(ChannelConfig.channel_id == channel_id)
        )
        await db.commit()


crud_channel_config = CRUDChannelConfig()
