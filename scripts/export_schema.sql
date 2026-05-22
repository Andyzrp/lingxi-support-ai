-- =============================================
-- 智能客服系统 - 数据库结构导出脚本
-- 用于从现有数据库导出结构，更新 init.sql
-- =============================================

-- 1. 查询所有表及其注释
\echo '======================================'
\echo '1. 所有表及注释'
\echo '======================================'
SELECT 
    t.table_name,
    obj_description((schemaname || '.' || table_name)::regclass, 'pg_class') AS table_comment
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
ORDER BY t.table_name;

-- 2. 查询所有列信息（完整结构）
\echo ''
\echo '======================================'
\echo '2. 所有列详细信息'
\echo '======================================'
SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    c.column_default,
    c.is_nullable,
    c.character_maximum_length,
    c.numeric_precision,
    c.numeric_scale,
    c.ordinal_position,
    col_description((schemaname || '.' || table_name)::regclass, c.ordinal_position) AS column_comment
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name AND t.table_schema = c.table_schema
WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name, c.ordinal_position;

-- 3. 查询所有主键
\echo ''
\echo '======================================'
\echo '3. 所有主键'
\echo '======================================'
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    kcu.ordinal_position
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name 
    AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.ordinal_position;

-- 4. 查询所有外键
\echo ''
\echo '======================================'
\echo '4. 所有外键'
\echo '======================================'
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name 
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name
    AND tc.table_schema = ccu.table_schema
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- 5. 查询所有索引（排除主键自带索引）
\echo ''
\echo '======================================'
\echo '5. 所有索引'
\echo '======================================'
SELECT
    tablename AS table_name,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 6. 查询所有唯一约束
\echo ''
\echo '======================================'
\echo '6. 所有唯一约束'
\echo '======================================'
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    kcu.ordinal_position
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name 
    AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'UNIQUE'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name, kcu.ordinal_position;

-- 7. 按表分组，生成 CREATE TABLE 语句（参考用）
\echo ''
\echo '======================================'
\echo '7. 各表完整结构（表名 + 列信息汇总）'
\echo '======================================'
SELECT 
    '=== ' || t.table_name || ' ===' AS info,
    string_agg(
        c.column_name || ' ' || 
        coalesce(c.data_type, '') ||
        CASE WHEN c.character_maximum_length IS NOT NULL THEN '(' || c.character_maximum_length || ')' ELSE '' END ||
        CASE WHEN c.numeric_precision IS NOT NULL AND c.numeric_scale IS NOT NULL THEN '(' || c.numeric_precision || ',' || c.numeric_scale || ')' ELSE '' END ||
        CASE WHEN c.column_default IS NOT NULL THEN ' DEFAULT ' || c.column_default ELSE '' END ||
        CASE WHEN c.is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END,
        ', '
        ORDER BY c.ordinal_position
    ) AS columns_def
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name AND t.table_schema = c.table_schema
WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
GROUP BY t.table_name
ORDER BY t.table_name;

-- 8. 查询 system_configs 表的数据
\echo ''
\echo '======================================'
\echo '8. system_configs 表数据'
\echo '======================================'
SELECT * FROM system_configs ORDER BY id;

-- 9. 查询 sequences 信息
\echo ''
\echo '======================================'
\echo '9. 所有序列'
\echo '======================================'
SELECT 
    sequence_name,
    start_value,
    minimum_value,
    maximum_value,
    increment_by
FROM information_schema.sequences
WHERE sequence_schema = 'public';

-- 10. 汇总统计
\echo ''
\echo '======================================'
\echo '10. 表统计'
\echo '======================================'
SELECT 
    'Tables: ' || COUNT(DISTINCT table_name) || 
    ', Columns: ' || COUNT(*) ||
    ', Indexes: ' || (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') ||
    ', Constraints: ' || (SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema = 'public')
AS summary
FROM information_schema.columns
WHERE table_schema = 'public';

\echo ''
\echo '======================================'
\echo '结构导出完成！'
\echo '======================================'
