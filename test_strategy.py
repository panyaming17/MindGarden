import requests
import json

# 测试添加策略接口
url = "http://localhost:8000/api/v1/admin/strategies"

# 策略数据（使用前端的请求体结构）
request_data = {
    "strategy_data": {
        "intensity_level": "高",
        "hedonic": "中性",
        "tension": "中",
        "complexity": "简单",
        "fusion_mode": "test3",
        "cbt_techniques": "test3",
        "tcm_methods": "test3",
        "strategy_content": "[测试方法] test3",
        "example": "测试示例3"
    },
    "request": {}
}

# 发送 POST 请求
response = requests.post(
    url,
    json=request_data,
    headers={"Content-Type": "application/json"}
)

# 打印响应
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")
