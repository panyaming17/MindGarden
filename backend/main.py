"""
后端服务主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入路由
from backend.api.v1.chat_endpoints import router as chat_router
from backend.api.v1.auth_endpoints import router as auth_router
from backend.api.v1.admin_endpoints import router as admin_router
from backend.api.v1.mood_endpoints import router as mood_router
from backend.api.v1.questionnaire_endpoints import router as questionnaire_router
from backend.api.v1.report_endpoints import router as report_router
from backend.api.v1.alert_endpoints import router as alert_router
from backend.api.v1.emotion_endpoints import router as emotion_router

# 创建FastAPI应用实例
app = FastAPI(
    title="心理AI助手API",
    description="提供心理辅导和情绪分析的API服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(mood_router)
app.include_router(questionnaire_router)
app.include_router(report_router)
app.include_router(alert_router)
app.include_router(emotion_router)

# 根路径
@app.get("/")
async def root():
    return {"message": "心理AI助手API服务正在运行"}

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
