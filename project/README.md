# 抑郁情绪智能疏导系统

一个基于 AI 多智能体系统的抑郁情绪智能疏导平台，结合中医情志理论和现代心理学 CBT 疗法，为用户提供专业的情绪疏导服务。

## 🌟 核心功能

### 1. 智能对话疏导
- **六阶段疏导流程**：建立关系 → 信息收集 → 深度探索 → 认知浮现 → 干预中 → 总结巩固
- **多智能体协作**：记录师 → 分析师 → 疏导师，专业化分工
- **实时情绪预测**：四维情绪预测（强度、愉悦度、紧张度、复杂度）
- **思维陷阱识别**：自动识别认知扭曲和思维陷阱

### 2. 情绪记录与管理
- 中医七情情绪标签（喜、怒、忧、思、悲、恐、惊）
- 情绪日历和时间线可视化
- 情绪健康趋势分析
- 智能提醒功能

### 3. 专业心理评估
- HAMD 抑郁量表评估
- 心理健康问卷
- 自动生成评估报告

### 4. 个性化干预方案
- 基于 CBT 疗法的认知重构建议
- 中医情志相胜疗法推荐
- 个性化疏导策略生成

### 5. 风险预警系统
- 实时对话风险监测
- 分级预警机制
- 高风险用户识别和管理

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI (Python 3.9+)
- **数据库**: MySQL 8.0+
- **向量数据库**: ChromaDB
- **LLM 集成**: 
  - 阿里云百炼（通义千问系列）
  - DeepSeek
  - 百度千帆（文心一言）
  - 智谱 AI（GLM）
- **AI/ML**: 
  - LangChain
  - Sentence Transformers
  - Scikit-learn
- **认证**: JWT (JSON Web Token)

### 前端技术栈
- **框架**: Vue 3 + Vite
- **状态管理**: Pinia
- **路由**: Vue Router
- **UI 组件**: 自定义组件库
- **HTTP 客户端**: Fetch API
- **构建工具**: Vite 5.0

### 核心架构
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  前端 (Vue3) │ ────▶│  后端 (FastAPI)│ ────▶│   LLM 服务   │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  状态管理   │      │  多智能体系统  │      │ 向量数据库  │
│   (Pinia)   │      │ (Agents)     │      │ (ChromaDB)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   MySQL DB   │
                     └──────────────┘
```

## 📦 项目结构

```
project/
├── backend/                 # 后端代码
│   ├── agents/             # 多智能体系统
│   │   ├── recorder_agent.py      # 记录师智能体
│   │   ├── analyst_agent.py       # 分析师智能体
│   │   └── therapist_agent.py     # 疏导师智能体
│   ├── api/                # API 路由
│   │   └── v1/            # API 版本 1
│   ├── core/              # 核心模块
│   │   ├── database.py    # 数据库连接
│   │   ├── llm_service.py # LLM 服务
│   │   └── memory_manager.py # 记忆管理
│   ├── models/            # 数据模型
│   ├── repositories/      # 数据访问层
│   ├── services/          # 业务逻辑层
│   │   ├── alert_service.py      # 预警服务
│   │   ├── emotion_rag_service.py # 情绪 RAG 服务
│   │   └── clinical_case_rag.py  # 临床案例 RAG
│   ├── main.py            # 应用入口
│   └── requirements.txt   # Python 依赖
├── frontend/              # 前端代码
│   ├── public/           # 静态资源
│   ├── src/              # 源代码
│   │   ├── components/   # Vue 组件
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── router/       # 路由配置
│   │   ├── utils/        # 工具函数
│   │   └── views/        # 页面视图
│   ├── index.html        # HTML 模板
│   ├── package.json      # Node.js 依赖
│   └── vite.config.js    # Vite 配置
├── .env.example          # 环境变量示例（后端）
├── .gitignore           # Git 忽略文件
└── README.md            # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Git

### 1. 克隆项目

```bash
git clone <repository-url>
cd project
```

### 2. 后端部署

#### 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 配置环境变量

```bash
# 复制环境变量示例文件
cp ../.env.example ../.env

# 编辑 .env 文件，填入你的配置
# - LLM API 密钥
# - 数据库连接信息
```

#### 初始化数据库

```bash
# 登录 MySQL 创建数据库
mysql -u root -p
CREATE DATABASE emotional_coaching_system_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 启动后端服务

```bash
# 开发环境
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

访问 `http://localhost:8000/docs` 查看 API 文档

### 3. 前端部署

#### 安装 Node.js 依赖

```bash
cd frontend
npm install
```

#### 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置 API 地址
```

#### 启动开发服务器

```bash
npm run dev
```

#### 构建生产版本

```bash
npm run build
```

## 📖 使用说明

### 用户端功能

1. **注册登录**: 创建账号并登录系统
2. **智能对话**: 与 AI 疏导师进行对话交流
3. **情绪记录**: 记录每日情绪状态
4. **心理评估**: 完成专业心理量表评估
5. **查看报告**: 查看情绪分析报告和疏导建议

### 管理端功能

1. **用户管理**: 查看和管理用户信息
2. **预警管理**: 处理用户风险预警
3. **问卷管理**: 管理心理评估问卷
4. **规则配置**: 配置预警规则和疏导策略

## 🔒 安全性说明

### 敏感信息保护

- ✅ API 密钥存储在 `.env` 文件中（不提交到 Git）
- ✅ 密码使用 bcrypt 加密存储
- ✅ JWT Token 认证机制
- ✅ CORS 跨域配置
- ✅ 敏感日志已移除

### 数据隐私

- 用户密码加密存储
- 对话记录加密传输
- 支持数据删除和导出

## 📄 许可证

本项目仅供学习和研究使用

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请提交 Issue。

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue 3](https://vuejs.org/)
- [LangChain](https://www.langchain.com/)
- [ChromaDB](https://www.trychroma.com/)
- [阿里云百炼](https://help.aliyun.com/zh/dashscope/)

---

**注意**: 本系统不能替代专业心理咨询服务。如有严重心理问题，请及时寻求专业心理咨询师帮助。
