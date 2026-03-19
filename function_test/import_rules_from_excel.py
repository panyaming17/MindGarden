import pandas as pd
import json
from backend.core.database import RuleDB, SessionLocal


def import_cbt_rules():
    """导入CBT策略库"""
    print("开始导入CBT策略库...")
    try:
        # 读取Excel文件
        df = pd.read_excel("CBT_策略库.xlsx")
        print(f"成功读取CBT策略库，共{len(df)}条记录")
        
        # 连接数据库
        db = SessionLocal()
        
        for index, row in df.iterrows():
            # 构建规则内容
            content = {
                "strategy": row.get("策略", ""),
                "description": row.get("描述", ""),
                "examples": row.get("示例", "").split("\n") if pd.notna(row.get("示例")) else []
            }
            
            # 创建规则
            rule = RuleDB(
                type="cbt",
                name=row.get("名称", f"CBT策略{index+1}"),
                content=content,
                version="1.0",
                is_active=True
            )
            
            db.add(rule)
        
        db.commit()
        print(f"成功导入{len(df)}条CBT策略")
        db.close()
    except Exception as e:
        print(f"导入CBT策略库失败: {str(e)}")


def import_tcm_rules():
    """导入中医情志规则库"""
    print("开始导入中医情志规则库...")
    try:
        # 读取Excel文件
        df = pd.read_excel("中医_情志规则库.xlsx")
        print(f"成功读取中医情志规则库，共{len(df)}条记录")
        
        # 连接数据库
        db = SessionLocal()
        
        for index, row in df.iterrows():
            # 构建规则内容
            content = {
                "emotion": row.get("情志", ""),
                "zang": row.get("脏腑", ""),
                "intervention": row.get("干预方法", ""),
                "herbs": row.get("推荐中药", "").split("\n") if pd.notna(row.get("推荐中药")) else [],
                "acupoints": row.get("推荐穴位", "").split("\n") if pd.notna(row.get("推荐穴位")) else []
            }
            
            # 创建规则
            rule = RuleDB(
                type="tcm",
                name=row.get("名称", f"中医情志规则{index+1}"),
                content=content,
                version="1.0",
                is_active=True
            )
            
            db.add(rule)
        
        db.commit()
        print(f"成功导入{len(df)}条中医情志规则")
        db.close()
    except Exception as e:
        print(f"导入中医情志规则库失败: {str(e)}")


if __name__ == "__main__":
    print("开始导入规则库...")
    import_cbt_rules()
    import_tcm_rules()
    print("规则库导入完成!")
