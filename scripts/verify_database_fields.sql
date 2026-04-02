-- 直接查询 session_analysis_insights 表结构
-- 在 Navicat 中执行这个 SQL 来验证字段是否存在

-- 方法 1: 查看表的所有列
SELECT 
    COLUMN_NAME AS '字段名',
    COLUMN_TYPE AS '数据类型',
    IS_NULLABLE AS '可为空',
    COLUMN_COMMENT AS '注释'
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'emotional_coaching_system_db'
  AND TABLE_NAME = 'session_analysis_insights'
ORDER BY ORDINAL_POSITION;

-- 方法 2: 检查新字段是否存在
SELECT 
    'intensity_values' AS '字段名',
    CASE WHEN COUNT(*) > 0 THEN '✓ 存在' ELSE '✗ 不存在' END AS '状态'
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'emotional_coaching_system_db'
  AND TABLE_NAME = 'session_analysis_insights'
  AND COLUMN_NAME = 'intensity_values'
UNION ALL
SELECT 
    'hedonic_counts',
    CASE WHEN COUNT(*) > 0 THEN '✓ 存在' ELSE '✗ 不存在' END
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'emotional_coaching_system_db'
  AND TABLE_NAME = 'session_analysis_insights'
  AND COLUMN_NAME = 'hedonic_counts'
UNION ALL
SELECT 
    'tension_counts',
    CASE WHEN COUNT(*) > 0 THEN '✓ 存在' ELSE '✗ 不存在' END
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'emotional_coaching_system_db'
  AND TABLE_NAME = 'session_analysis_insights'
  AND COLUMN_NAME = 'tension_counts'
UNION ALL
SELECT 
    'complexity_analysis',
    CASE WHEN COUNT(*) > 0 THEN '✓ 存在' ELSE '✗ 不存在' END
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'emotional_coaching_system_db'
  AND TABLE_NAME = 'session_analysis_insights'
  AND COLUMN_NAME = 'complexity_analysis'
UNION ALL
SELECT 
    'is_completed',
    CASE WHEN COUNT(*) > 0 THEN '✓ 存在' ELSE '✗ 不存在' END
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'emotional_coaching_system_db'
  AND TABLE_NAME = 'session_analysis_insights'
  AND COLUMN_NAME = 'is_completed'
UNION ALL
SELECT 
    'is_migrated',
    CASE WHEN COUNT(*) > 0 THEN '✓ 存在' ELSE '✗ 不存在' END
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'emotional_coaching_system_db'
  AND TABLE_NAME = 'session_analysis_insights'
  AND COLUMN_NAME = 'is_migrated';
