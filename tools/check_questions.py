"""查看问卷题目"""
from backend.core.database import SessionLocal, QuestionnaireTemplateDB

db = SessionLocal()

print('=== PHQ-9 抑郁量表题目 ===')
phq9 = db.query(QuestionnaireTemplateDB).filter(QuestionnaireTemplateDB.code == 'PHQ9').first()
if phq9 and phq9.questions:
    for i, q in enumerate(phq9.questions, 1):
        print(f"\n{i}. {q['text']}")
        print(f"   选项:")
        for opt in q['options']:
            print(f"     - {opt['label']} ({opt['desc']}): {opt['score']}分")
else:
    print('  (无题目数据)')

print('\n' + '='*60)
print('=== GAD-7 焦虑量表题目 ===')
gad7 = db.query(QuestionnaireTemplateDB).filter(QuestionnaireTemplateDB.code == 'GAD7').first()
if gad7 and gad7.questions:
    for i, q in enumerate(gad7.questions, 1):
        print(f"\n{i}. {q['text']}")
        print(f"   选项:")
        for opt in q['options']:
            print(f"     - {opt['label']} ({opt['desc']}): {opt['score']}分")
else:
    print('  (无题目数据)')

db.close()
