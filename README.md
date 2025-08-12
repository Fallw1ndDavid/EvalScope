# 大模型数据处理系统

用来管理大模型内的语料信息，包括语料的上传、下载、删除、查询等功能。

## 项目结构

- `frontend/` - Vue3前端应用
- `backend/` - Python后端服务
- `data/` - 数据存储目录

## 功能说明

### 格式转换
1. CSV转换表单：
   - 上传CSV文件
   - 字段映射配置
   - 导出JSONL文件
2. 转换后的列表：
   - 显示历史转换记录
   - 支持下载CSV和JSONL文件

### 提示词管理
- 添加/删除/查询/修改提示词
- 提示词表单由标题和内容组成

## 技术栈

### 前端
- Vue 3
- Vite
- Element Plus
- Vue Router

### 后端
- Python 3.7+
- FastAPI
- Uvicorn
- Pandas

## 快速开始

1. 启动后端服务：
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. 启动前端开发服务器：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. 打开浏览器访问 http://localhost:3000