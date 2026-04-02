-- ========================================
-- 数据库优化迁移脚本
-- 版本：1.0
-- 日期：2026-04-01
-- 描述：删除冗余表，添加增量聚合字段
-- ========================================

-- 开始事务
BEGIN;

-- ========================================
-- 第一步：删除冗余表
-- ========================================

-- 删除 session_four_dim_data 表
DROP TABLE IF EXISTS session_four_dim_data;
PRINT '已删除 session_four_dim_data 表';

-- 删除 questionnaires 表
DROP TABLE IF EXISTS questionnaires;
PRINT '已删除 questionnaires 表';

-- 删除 user_questionnaire_results 表
DROP TABLE IF EXISTS user_questionnaire_results;
PRINT '已删除 user_questionnaire_results 表';

-- ========================================
-- 第二步：修改 session_analysis_insights 表结构
-- ========================================

-- 添加四维数据增量统计字段
ALTER TABLE session_analysis_insights 
ADD intensity_values NVARCHAR(MAX) NULL;
PRINT '已添加 intensity_values 字段';

ALTER TABLE session_analysis_insights 
ADD hedonic_counts NVARCHAR(MAX) NULL;
PRINT '已添加 hedonic_counts 字段';

ALTER TABLE session_analysis_insights 
ADD tension_counts NVARCHAR(MAX) NULL;
PRINT '已添加 tension_counts 字段';

ALTER TABLE session_analysis_insights 
ADD complexity_analysis NVARCHAR(MAX) NULL;
PRINT '已添加 complexity_analysis 字段';

-- 添加状态标记字段
ALTER TABLE session_analysis_insights 
ADD is_completed BIT DEFAULT 0;
PRINT '已添加 is_completed 字段';

ALTER TABLE session_analysis_insights 
ADD is_migrated BIT DEFAULT 0;
PRINT '已添加 is_migrated 字段';

-- ========================================
-- 第三步：添加注释说明（SQL Server 语法）
-- ========================================

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'session_analysis_insights',
    @level2type = N'COLUMN', @level2name = 'intensity_values',
    @value = N'强度值数组 [{"value": 6.5, "timestamp": "..."}, ...]';
PRINT '已添加 intensity_values 注释';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'session_analysis_insights',
    @level2type = N'COLUMN', @level2name = 'hedonic_counts',
    @value = N'快感度计数 {"负性": 3, "中性": 1, "正性": 1}';
PRINT '已添加 hedonic_counts 注释';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'session_analysis_insights',
    @level2type = N'COLUMN', @level2name = 'tension_counts',
    @value = N'紧张度计数 {"高": 1, "中": 1, "低": 3}';
PRINT '已添加 tension_counts 注释';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'session_analysis_insights',
    @level2type = N'COLUMN', @level2name = 'complexity_analysis',
    @value = N'复杂度分析 {"type": "复杂", "emotions": [...]}';
PRINT '已添加 complexity_analysis 注释';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'session_analysis_insights',
    @level2type = N'COLUMN', @level2name = 'is_completed',
    @value = N'是否已完成分析';
PRINT '已添加 is_completed 注释';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'session_analysis_insights',
    @level2type = N'COLUMN', @level2name = 'is_migrated',
    @value = N'是否已迁移到 session_reports';
PRINT '已添加 is_migrated 注释';

-- ========================================
-- 第四步：验证迁移
-- ========================================

-- 检查表是否已删除
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'session_four_dim_data')
    PRINT '✓ session_four_dim_data 表已成功删除';
ELSE
    PRINT '✗ session_four_dim_data 表删除失败';

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'questionnaires')
    PRINT '✓ questionnaires 表已成功删除';
ELSE
    PRINT '✗ questionnaires 表删除失败';

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_questionnaire_results')
    PRINT '✓ user_questionnaire_results 表已成功删除';
ELSE
    PRINT '✗ user_questionnaire_results 表删除失败';

-- 检查新字段是否已添加
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('session_analysis_insights') AND name = 'intensity_values')
    PRINT '✓ intensity_values 字段已成功添加';
ELSE
    PRINT '✗ intensity_values 字段添加失败';

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('session_analysis_insights') AND name = 'hedonic_counts')
    PRINT '✓ hedonic_counts 字段已成功添加';
ELSE
    PRINT '✗ hedonic_counts 字段添加失败';

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('session_analysis_insights') AND name = 'tension_counts')
    PRINT '✓ tension_counts 字段已成功添加';
ELSE
    PRINT '✗ tension_counts 字段添加失败';

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('session_analysis_insights') AND name = 'complexity_analysis')
    PRINT '✓ complexity_analysis 字段已成功添加';
ELSE
    PRINT '✗ complexity_analysis 字段添加失败';

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('session_analysis_insights') AND name = 'is_completed')
    PRINT '✓ is_completed 字段已成功添加';
ELSE
    PRINT '✗ is_completed 字段添加失败';

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('session_analysis_insights') AND name = 'is_migrated')
    PRINT '✓ is_migrated 字段已成功添加';
ELSE
    PRINT '✗ is_migrated 字段添加失败';

-- 提交事务
COMMIT;
PRINT '========================================';
PRINT '数据库迁移完成！';
PRINT '========================================';
