#########       主应用       ###########
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
from backend.api.v1 import auth_endpoints, chat_endpoints, report_endpoints, mood_endpoints, questionnaire_endpoints, alert_endpoints, admin_endpoints

app = FastAPI(
    title="抑郁情绪智能疏导系统",
    description="基于CBT与中医情志双通路的抑郁情绪智能疏导系统",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_endpoints.router)
app.include_router(chat_endpoints.router)
app.include_router(report_endpoints.router)
app.include_router(mood_endpoints.router)
app.include_router(questionnaire_endpoints.router)
app.include_router(alert_endpoints.router)
app.include_router(admin_endpoints.router)

@app.get("/")
async def root():
    return {
        "service": "analyst_module",
        "status": "active",
        "description": "双通路情绪分析服务"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,  # 标准端口
        reload=True
    )
