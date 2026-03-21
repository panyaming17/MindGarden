### 1.遇到paraphrase-multilingual-MiniLM-L12-v2模型加载失败
#### 问题描述
````powershell
Loading SentenceTransformer model...
'[WinError 10060] 由于连接方在一段时间后没有正确答复或连接的主机没有反应，连接尝试失败。' thrown while requesting HEAD https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main/./modules.json
Retrying in 1s [Retry 1/5].
````
#### 解决方法
1. 检查网络连接是否正常
2. 尝试使用其他网络环境
3. 等待一段时间后重试
4. 尝试使用镜像加速加载模型:
```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
```
