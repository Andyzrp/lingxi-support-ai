from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

LABEL_MAP = {"good": 0, "bad": 1, "neutral": 2}
LABEL_REVERSE = {0: "good", 1: "bad", 2: "neutral"}


def _map_label_to_type(label: str) -> int:
    return LABEL_MAP.get(label, 2)


def _map_type_to_label(annotation_type: int) -> str:
    return LABEL_REVERSE.get(annotation_type, "neutral")


def _row_to_dict(row) -> dict:
    d = dict(row._mapping)
    if "annotation_type" in d:
        d["label"] = _map_type_to_label(d.pop("annotation_type"))
    if "annotated_by" in d:
        d["annotator_id"] = d.pop("annotated_by")
    if "annotation_note" in d:
        d["remark"] = d.pop("annotation_note")
    return d


# ==================== 创建标注 ====================


async def create_annotation(
    db: AsyncSession,
    conversation_id: int,
    message_id: int,
    annotator_id: int,
    label: str,
    correct_answer: Optional[str] = None,
    remark: Optional[str] = None,
) -> dict:
    """
    创建标注记录
    同一条消息已存在标注时执行 UPSERT
    """
    annotation_type = _map_label_to_type(label)

    sql = text("""
        INSERT INTO annotation_records (
            conversation_id,
            message_id,
            annotated_by,
            annotation_type,
            correct_answer,
            annotation_note,
            created_at,
            updated_at
        ) VALUES (
            :conversation_id,
            :message_id,
            :annotated_by,
            :annotation_type,
            :correct_answer,
            :annotation_note,
            NOW(),
            NOW()
        )
        ON CONFLICT (message_id)
        DO UPDATE SET
            annotation_type = EXCLUDED.annotation_type,
            correct_answer  = EXCLUDED.correct_answer,
            annotation_note = EXCLUDED.annotation_note,
            annotated_by    = EXCLUDED.annotated_by,
            updated_at      = NOW()
        RETURNING
            id, conversation_id, message_id,
            annotated_by, annotation_type, correct_answer,
            annotation_note, created_at, updated_at
    """)
    res = await db.execute(
        sql,
        {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "annotated_by": annotator_id,
            "annotation_type": annotation_type,
            "correct_answer": correct_answer,
            "annotation_note": remark,
        },
    )
    await db.commit()
    row = res.fetchone()
    return _row_to_dict(row) if row else {}


# ==================== 查询标注列表 ====================


async def get_annotations(
    db: AsyncSession,
    conversation_id: Optional[int] = None,
    label: Optional[str] = None,
    annotator_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[dict], int]:
    """
    查询标注列表，支持按会话 / 标签 / 标注人筛选
    返回 (records, total)
    """
    conditions = ["1=1"]
    params = {}

    if conversation_id:
        conditions.append("a.conversation_id = :conversation_id")
        params["conversation_id"] = conversation_id

    if label:
        annotation_type = _map_label_to_type(label)
        conditions.append("a.annotation_type = :annotation_type")
        params["annotation_type"] = annotation_type

    if annotator_id:
        conditions.append("a.annotated_by = :annotator_id")
        params["annotator_id"] = annotator_id

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    count_sql = text(f"""
        SELECT COUNT(*) AS cnt
        FROM annotation_records a
        WHERE {where}
    """)
    count_res = await db.execute(count_sql, params)
    total = count_res.scalar() or 0

    list_sql = text(f"""
        SELECT
            a.id,
            a.conversation_id,
            a.message_id,
            a.annotated_by,
            ad.nickname          AS annotator_name,
            a.annotation_type,
            a.correct_answer,
            a.annotation_note,
            m.content            AS original_content,
            a.created_at,
            a.updated_at
        FROM annotation_records a
        LEFT JOIN admins  ad ON ad.id = a.annotated_by
        LEFT JOIN messages m ON m.id  = a.message_id
        WHERE {where}
        ORDER BY a.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    list_res = await db.execute(
        list_sql,
        {
            **params,
            "limit": page_size,
            "offset": offset,
        },
    )
    rows = list_res.fetchall()
    return [_row_to_dict(r) for r in rows], total


# ==================== 查询单条标注 ====================


async def get_annotation_by_message(
    db: AsyncSession,
    message_id: int,
) -> Optional[dict]:
    """根据消息 ID 查询已有标注"""
    sql = text("""
        SELECT
            id, conversation_id, message_id,
            annotated_by, annotation_type, correct_answer,
            annotation_note, created_at, updated_at
        FROM annotation_records
        WHERE message_id = :message_id
        LIMIT 1
    """)
    res = await db.execute(sql, {"message_id": message_id})
    row = res.fetchone()
    return _row_to_dict(row) if row else None


# ==================== 更新标注 ====================


async def update_annotation(
    db: AsyncSession,
    annotation_id: int,
    annotator_id: int,
    label: Optional[str] = None,
    correct_answer: Optional[str] = None,
    remark: Optional[str] = None,
) -> Optional[dict]:
    """更新标注记录"""
    set_parts = ["updated_at = NOW()", "annotated_by = :annotated_by"]
    params = {"annotation_id": annotation_id, "annotated_by": annotator_id}

    if label is not None:
        set_parts.append("annotation_type = :annotation_type")
        params["annotation_type"] = _map_label_to_type(label)

    if correct_answer is not None:
        set_parts.append("correct_answer = :correct_answer")
        params["correct_answer"] = correct_answer

    if remark is not None:
        set_parts.append("annotation_note = :annotation_note")
        params["annotation_note"] = remark

    sql = text(f"""
        UPDATE annotation_records
        SET {", ".join(set_parts)}
        WHERE id = :annotation_id
        RETURNING
            id, conversation_id, message_id,
            annotated_by, annotation_type, correct_answer,
            annotation_note, created_at, updated_at
    """)
    res = await db.execute(sql, params)
    await db.commit()
    row = res.fetchone()
    return _row_to_dict(row) if row else None


# ==================== 删除标注 ====================


async def delete_annotation(
    db: AsyncSession,
    annotation_id: int,
) -> bool:
    """删除标注记录"""
    sql = text("""
        DELETE FROM annotation_records
        WHERE id = :annotation_id
        RETURNING id
    """)
    res = await db.execute(sql, {"annotation_id": annotation_id})
    await db.commit()
    return res.fetchone() is not None


# ==================== 标注统计 ====================


async def get_annotation_stats(
    db: AsyncSession,
    conversation_id: Optional[int] = None,
) -> dict:
    """获取标注统计数据"""
    condition = ""
    params = {}

    if conversation_id:
        condition = "WHERE conversation_id = :conversation_id"
        params["conversation_id"] = conversation_id

    sql = text(f"""
        SELECT
            COUNT(*)                                              AS total,
            COUNT(*) FILTER (WHERE annotation_type = 0)          AS good,
            COUNT(*) FILTER (WHERE annotation_type = 1)          AS bad,
            COUNT(*) FILTER (WHERE annotation_type = 2)          AS neutral
        FROM annotation_records
        {condition}
    """)
    res = await db.execute(sql, params)
    row = res.fetchone()

    total = row.total or 0
    good = row.good or 0
    bad = row.bad or 0
    neutral = row.neutral or 0

    return {
        "total": total,
        "good": good,
        "bad": bad,
        "neutral": neutral,
        "good_rate": round(good / total, 4) if total > 0 else 0.0,
        "bad_rate": round(bad / total, 4) if total > 0 else 0.0,
    }
