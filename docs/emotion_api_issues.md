# 情绪记录失败问题分析

## 问题现象
从控制台错误信息可以看到，所有情绪相关的 API 请求都失败了，错误信息为：
- `Failed to load resource: net::ERR_CONNECTION_REFUSED`
- `TypeError: Failed to fetch`

具体失败的 API 端点包括：
- `http://localhost:8000/api/emotions/record`
- `http://localhost:8000/api/emotions/history`
- `http://localhost:8000/api/alerts`

## 可能原因分析

### 1. 后端服务器未启动
- **现象**：前端无法连接到 `localhost:8000`
- **验证方法**：
  - 检查后端服务器是否正在运行
  - 尝试在浏览器中直接访问 `http://localhost:8000`
  - 检查后端服务器的启动日志

### 2. 后端服务器端口配置错误
- **现象**：后端服务器可能运行在其他端口上
- **验证方法**：
  - 检查后端服务器的配置文件，确认监听端口
  - 尝试访问其他可能的端口（如 8080、3000 等）

### 3. 后端服务器启动失败
- **现象**：后端服务器启动过程中出现错误
- **验证方法**：
  - 检查后端服务器的启动日志，查找错误信息
  - 确认后端依赖是否正确安装
  - 检查数据库连接是否正常

### 4. 网络连接问题
- **现象**：本地网络环境问题
- **验证方法**：
  - 检查网络连接状态
  - 尝试 ping localhost
  - 检查防火墙设置

### 5. API 路径配置错误
- **现象**：前端 API 路径与后端实际路径不匹配
- **验证方法**：
  - 检查前端 `emotion.js` 中的 API 路径配置
  - 确认后端 API 路由是否正确配置

## 前端代码分析

### API 基础配置
```javascript
// API 基础配置
const API_BASE_URL = 'http://localhost:8000'
```

### 情绪记录 API 调用
```javascript
// 记录情绪
const recordEmotion = async (data) => {
  try {
    isLoading.value = true
    const result = await request('/api/emotions/record', {
      method: 'POST',
      body: JSON.stringify(data)
    })
    // 刷新记录和统计数据
    await fetchRecords()
    await fetchStatistics()
    await checkRemind()
    return result
  } catch (error) {
    console.error('记录情绪失败:', error)
    throw error
  } finally {
    isLoading.value = false
  }
}
```

### 通用请求函数
```javascript
const request = async (url, options = {}) => {
  try {
    const { params, ...fetchOptions } = options
    
    let fullUrl = `${API_BASE_URL}${url}`
    // ... 省略参数处理代码 ...

    const response = await fetch(fullUrl, {
      ...fetchOptions,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
        ...fetchOptions.headers
      }
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || data.detail || '请求失败')
    }

    return data
  } catch (error) {
    console.error('API 请求失败:', error)
    throw error
  }
}
```

## 检查步骤

1. **检查后端服务器状态**
   - 确认后端服务是否启动
   - 检查后端服务日志
   - 验证后端服务是否在 8000 端口运行

2. **验证 API 端点**
   - 使用 Postman 或 curl 测试 API 端点
   - 确认 API 路径是否正确

3. **检查网络连接**
   - 确认本地网络连接正常
   - 检查防火墙设置

4. **检查数据库连接**
   - 确认后端数据库连接正常
   - 检查数据库服务是否运行

5. **检查前端配置**
   - 确认 `API_BASE_URL` 配置正确
   - 检查 token 获取是否正常

## 解决方案

1. **启动后端服务器**
   - 运行后端服务启动命令
   - 确保服务正常运行在 8000 端口

2. **调整端口配置**
   - 如果后端服务运行在其他端口，修改前端 `API_BASE_URL`

3. **修复后端服务问题**
   - 解决后端服务启动失败的问题
   - 确保数据库连接正常

4. **检查网络设置**
   - 确保本地网络连接正常
   - 检查防火墙是否阻止了连接

## 后端需要确认的问题

1. **服务状态**
   - 后端服务是否正常启动？
   - 服务是否运行在 8000 端口？

2. **API 端点**
   - `/api/emotions/record` 端点是否存在？
   - API 路由配置是否正确？

3. **数据库连接**
   - 数据库服务是否运行？
   - 数据库连接配置是否正确？

4. **认证机制**
   - JWT token 验证是否正常？
   - 权限配置是否正确？

5. **错误处理**
   - 后端是否有适当的错误处理机制？
   - 错误日志是否完整？

## 结论

情绪记录失败的主要原因是前端无法连接到后端服务器。需要先确保后端服务正常运行，然后再检查其他可能的问题。