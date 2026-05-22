# backend/app/crud/agent.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from typing import Optional, List
from datetime import datetime

from app.models.agent import Agent, AgentVersion, AgentConfig
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentVersionCreate,
    AgentConfigUpdate,
)


class CRUDAgent:
    async def create(
        self,
        db: AsyncSession,
        obj_in: AgentCreate,
    ) -> Agent:
        # ✅ agents表没有bot_id字段！bot通过agent_config关联
        db_obj = Agent(
            name=obj_in.name,
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
        agent_id: int,
    ) -> Optional[Agent]:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
    ) -> List[Agent]:
        result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        agent_id: int,
        obj_in: AgentUpdate,
    ) -> Optional[Agent]:
        update_data = {}
        if obj_in.name is not None:
            update_data["name"] = obj_in.name
        if obj_in.description is not None:
            update_data["description"] = obj_in.description
        if obj_in.status is not None:
            update_data["status"] = int(obj_in.status)

        if not update_data:
            return await self.get(db, agent_id)

        await db.execute(
            update(Agent).where(Agent.id == agent_id).values(**update_data)
        )
        await db.commit()
        return await self.get(db, agent_id)

    async def delete(self, db: AsyncSession, agent_id: int) -> bool:
        from app.models.agent import Agent, AgentVersion, AgentConfig
        from sqlalchemy import update

        await db.execute(
            update(Agent)
            .where(Agent.id == agent_id)
            .values(
                draft_version_id=None,
                current_version_id=None,
            )
        )
        await db.execute(
            delete(AgentConfig).where(
                AgentConfig.agent_version_id.in_(
                    select(AgentVersion.id).where(AgentVersion.agent_id == agent_id)
                )
            )
        )
        await db.execute(delete(AgentVersion).where(AgentVersion.agent_id == agent_id))
        result = await db.execute(delete(Agent).where(Agent.id == agent_id))
        await db.commit()
        return result.rowcount > 0

    async def set_current_version(
        self,
        db: AsyncSession,
        agent_id: int,
        version_id: int,
    ):
        await db.execute(
            update(Agent)
            .where(Agent.id == agent_id)
            .values(current_version_id=version_id)
        )
        await db.commit()

    async def set_draft_version(
        self,
        db: AsyncSession,
        agent_id: int,
        version_id: Optional[int],
    ):
        await db.execute(
            update(Agent)
            .where(Agent.id == agent_id)
            .values(draft_version_id=version_id)
        )
        await db.commit()


class CRUDAgentVersion:
    async def create(
        self,
        db: AsyncSession,
        agent_id: int,
        obj_in: AgentVersionCreate,
    ) -> AgentVersion:
        # ✅ version_no是VARCHAR(20)，不是INT
        result = await db.execute(
            select(func.count(AgentVersion.id)).where(AgentVersion.agent_id == agent_id)
        )
        count = result.scalar() or 0
        version_no = f"v{count + 1}.0"

        db_obj = AgentVersion(
            agent_id=agent_id,
            version_no=version_no,
            status=0,  # 草稿
            remark=obj_in.description,  # ✅ description → remark
        )
        db.add(db_obj)
        await db.flush()

        # 更新agent的draft_version_id
        await db.execute(
            update(Agent).where(Agent.id == agent_id).values(draft_version_id=db_obj.id)
        )

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(
        self,
        db: AsyncSession,
        version_id: int,
    ) -> Optional[AgentVersion]:
        result = await db.execute(
            select(AgentVersion).where(AgentVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        agent_id: int,
    ) -> List[AgentVersion]:
        result = await db.execute(
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
            .order_by(AgentVersion.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_draft(
        self,
        db: AsyncSession,
        agent_id: int,
    ) -> Optional[AgentVersion]:
        result = await db.execute(
            select(AgentVersion).where(
                and_(
                    AgentVersion.agent_id == agent_id,
                    AgentVersion.status == 0,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_published(
        self,
        db: AsyncSession,
        agent_id: int,
    ) -> Optional[AgentVersion]:
        result = await db.execute(
            select(AgentVersion)
            .where(
                and_(
                    AgentVersion.agent_id == agent_id,
                    AgentVersion.status == 1,
                )
            )
            .order_by(AgentVersion.published_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def publish(
        self,
        db: AsyncSession,
        agent_id: int,
        version_id: int,
    ) -> Optional[AgentVersion]:
        now = datetime.utcnow()

        # 归档当前发布版本
        await db.execute(
            update(AgentVersion)
            .where(
                and_(
                    AgentVersion.agent_id == agent_id,
                    AgentVersion.status == 1,
                )
            )
            .values(status=2)
        )

        # 发布新版本
        await db.execute(
            update(AgentVersion)
            .where(AgentVersion.id == version_id)
            .values(status=1, published_at=now)
        )

        # 更新agent的version引用
        await db.execute(
            update(Agent)
            .where(Agent.id == agent_id)
            .values(
                current_version_id=version_id,
                draft_version_id=None,
            )
        )

        await db.commit()
        return await self.get(db, version_id)

    async def rollback(
        self,
        db: AsyncSession,
        agent_id: int,
        version_id: int,
    ) -> Optional[AgentVersion]:
        now = datetime.utcnow()

        # 归档当前发布版本
        await db.execute(
            update(AgentVersion)
            .where(
                and_(
                    AgentVersion.agent_id == agent_id,
                    AgentVersion.status == 1,
                )
            )
            .values(status=2)
        )

        # 重新发布目标版本
        await db.execute(
            update(AgentVersion)
            .where(AgentVersion.id == version_id)
            .values(status=1, published_at=now)
        )

        # 更新agent的current_version_id
        await db.execute(
            update(Agent)
            .where(Agent.id == agent_id)
            .values(current_version_id=version_id)
        )

        await db.commit()
        return await self.get(db, version_id)


class CRUDAgentConfig:
    async def get_or_create(
        self,
        db: AsyncSession,
        agent_version_id: int,
        knowledge_base_id: Optional[int] = None,
    ) -> AgentConfig:
        result = await db.execute(
            select(AgentConfig).where(AgentConfig.agent_version_id == agent_version_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            config = AgentConfig(
                agent_version_id=agent_version_id,
                knowledge_base_id=knowledge_base_id,
                model_type=0,
                rag_threshold=0.75,
                context_rounds=3,
                emotion_detection=1,
                auto_transfer=1,
                auto_transfer_count=3,
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)

        return config

    async def update(
        self,
        db: AsyncSession,
        agent_version_id: int,
        obj_in: AgentConfigUpdate,
    ) -> AgentConfig:
        config = await self.get_or_create(db, agent_version_id)
        update_data = {}

        if obj_in.system_prompt is not None:
            update_data["system_prompt"] = obj_in.system_prompt
        if obj_in.knowledge_base_id is not None:
            update_data["knowledge_base_id"] = obj_in.knowledge_base_id
        if obj_in.no_answer_threshold is not None:
            update_data["auto_transfer_count"] = obj_in.no_answer_threshold

        if (
            obj_in.model is not None
            or obj_in.temperature is not None
            or obj_in.max_tokens is not None
        ):
            existing_params = config.model_params or {}
            if obj_in.model is not None:
                existing_params["model"] = obj_in.model
            if obj_in.temperature is not None:
                existing_params["temperature"] = obj_in.temperature
            if obj_in.max_tokens is not None:
                existing_params["max_tokens"] = obj_in.max_tokens
            update_data["model_params"] = existing_params

        if obj_in.tools_enabled is not None:
            update_data["tools_config"] = {"enabled_tools": obj_in.tools_enabled}

        if obj_in.transfer_keywords is not None:
            update_data["complaint_keywords"] = {
                "transfer_keywords": obj_in.transfer_keywords
            }

        if update_data:
            from sqlalchemy import update as sa_update

            await db.execute(
                sa_update(AgentConfig)
                .where(AgentConfig.agent_version_id == agent_version_id)
                .values(**update_data)
            )
            await db.commit()

        return await self.get_or_create(db, agent_version_id)


crud_agent = CRUDAgent()
crud_agent_version = CRUDAgentVersion()
crud_agent_config = CRUDAgentConfig()
