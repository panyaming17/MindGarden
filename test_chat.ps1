# 测试健康检查
Write-Host "测试服务健康状态..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
    Write-Host "✅ 服务运行正常 (状态码：$($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ 服务未运行：$_" -ForegroundColor Red
    exit 1
}

# 测试登录
Write-Host "`n测试登录..." -ForegroundColor Cyan
try {
    $body = @{
        username = "pym"
        password = "pym123456"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30 -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    $userId = $result.user.id
    Write-Host "✅ 登录成功 (用户 ID: $userId)" -ForegroundColor Green
} catch {
    Write-Host "❌ 登录失败：$_" -ForegroundColor Red
    exit 1
}

# 测试发送消息
Write-Host "`n测试发送消息..." -ForegroundColor Cyan
try {
    $body = @{
        user_id = $userId
        session_id = "test_session_001"
        message = "我最近感到压力很大"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/chat/message" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 60 -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    Write-Host "✅ 发送消息成功" -ForegroundColor Green
    Write-Host "回复：$($result.reply)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ 发送消息失败：$_" -ForegroundColor Red
    Write-Host "错误详情：$($_.Exception.Response.StatusCode)" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ 所有测试通过！" -ForegroundColor Green
