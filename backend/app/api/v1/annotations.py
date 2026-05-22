from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import success_response
from app.utils.response import PageResponse
from app.api.deps import get_current_admin
from app.schemas.annotation import (
    AnnotationCreateSchema,
    AnnotationUpdateSchema,
)
from app.crud import annotation as crud_annotation

router = APIRouter(tags=["数据标注"])


# ==================== 创建标注 ====================


@router.post("")
async def create_annotation(
    body: AnnotationCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """
    创建 / 更新标注记录
    同一条消息重复提交时自动覆盖（UPSERT）
    """
    from sqlalchemy import text

    check_sql = text("""
        SELECT id FROM messages
        WHERE id = :message_id
          AND conversation_id = :conversation_id
        LIMIT 1
    """)
    check_res = await db.execute(
        check_sql,
        {
            "message_id": body.message_id,
            "conversation_id": body.conversation_id,
        },
    )
    if not check_res.fetchone():
        raise HTTPException(status_code=404, detail="消息不存在或不属于该会话")

    record = await crud_annotation.create_annotation(
        db=db,
        conversation_id=body.conversation_id,
        message_id=body.message_id,
        annotator_id=current_admin.id,
        label=body.label,
        correct_answer=body.correct_answer,
        remark=body.remark,
    )
    return success_response(
        message="标注成功",
        data=record,
    )


# ==================== 查询标注列表 ====================


@router.get("")
async def get_annotations(
    conversation_id: Optional[int] = Query(None, description="按会话筛选"),
    label: Optional[str] = Query(None, description="按标签筛选：good/bad/neutral"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """查询标注记录列表"""
    records, total = await crud_annotation.get_annotations(
        db=db,
        conversation_id=conversation_id,
        label=label,
        page=page,
        page_size=page_size,
    )
    return PageResponse.success(
        data=records,
        total=total,
        page=page,
        page_size=page_size,
    )


# ==================== 查询消息标注状态 ====================


@router.get("/message/{message_id}")
async def get_message_annotation(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    查询指定消息的标注状态
    用于在会话详情页回显已标注内容
    """
    record = await crud_annotation.get_annotation_by_message(
        db=db,
        message_id=message_id,
    )
    return success_response(data=record)


# ==================== 更新标注 ====================


@router.put("/{annotation_id}")
async def update_annotation(
    annotation_id: int,
    body: AnnotationUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """更新已有标注记录"""
    record = await crud_annotation.update_annotation(
        db=db,
        annotation_id=annotation_id,
        annotator_id=current_admin.id,
        label=body.label,
        correct_answer=body.correct_answer,
        remark=body.remark,
    )
    if not record:
        raise HTTPException(status_code=404, detail="标注记录不存在")

    return success_response(
        message="更新成功",
        data=record,
    )


# ==================== 删除标注 ====================


@router.delete("/{annotation_id}")
async def delete_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """删除标注记录"""
    ok = await crud_annotation.delete_annotation(
        db=db,
        annotation_id=annotation_id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="标注记录不存在")

    return success_response(message="删除成功")


# ==================== 标注统计 ====================


@router.get("/stats")
async def get_annotation_stats(
    conversation_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    获取标注统计数据
    返回 good / bad / neutral 数量及占比
    """
    stats = await crud_annotation.get_annotation_stats(
        db=db,
        conversation_id=conversation_id,
    )
    return success_response(data=stats)
