#########       主应用       ###########
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
from backend.api import analyst_endpoints, recorder_endpoints, therapist_endpoints, conversation_endpoints, auth_endpoints, admin_endpoints, rule_endpoints, dialogue_endpoints

app = FastAPI(
    title="抑郁情绪智能疏导系统 - 分析师模块",
    description="负责CBT与中医情志双通路分析的后端模块",
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
app.include_router(analyst_endpoints.router)
app.include_router(recorder_endpoints.router)
app.include_router(therapist_endpoints.router)
app.include_router(conversation_endpoints.router)
app.include_router(auth_endpoints.router)
app.include_router(admin_endpoints.router)
app.include_router(rule_endpoints.router)
app.include_router(dialogue_endpoints.router)

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
        port=8001,  # 分析师模块专用端口
        reload=True
    )
