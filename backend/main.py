from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import os
import glob
from typing import List
import jsonlines
import httpx
import json
import asyncio
from pydantic import BaseModel, Field
from datetime import datetime
import httpx
import jsonlines
import csv
import re
from typing import Dict, Any, List, Optional
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
import logging

# 全局配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

app = FastAPI()

# 添加CORS中间件以允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据存储目录
# 使用绝对路径指向项目根目录下的data文件夹
# 使用__file__获取当前脚本所在目录，然后向上一级找到项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# NGINX日志解析目录
NGINX_LOGS_DIR = os.path.join(DATA_DIR, 'nginx_logs')
if not os.path.exists(NGINX_LOGS_DIR):
    os.makedirs(NGINX_LOGS_DIR)

# 数据文件路径
PROMPTS_FILE = os.path.join(DATA_DIR, 'prompts', 'prompts.json')
CONVERSION_RECORDS_FILE = os.path.join(DATA_DIR, 'conversion_records.json')
# 修正模型文件路径，指向项目根目录下的data文件夹
# 使用__file__获取当前脚本所在目录，然后向上两级找到项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODELS_FILE = os.path.join(PROJECT_ROOT, 'data', 'models', 'models.json')

# 加载数据
def load_data():
    global prompts_data, conversion_records_data, models_data
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            prompts_data = json.load(f)
    else:
        # 如果文件不存在，初始化为空数组并保存
        prompts_data = []
        save_prompts_data()
    
    if os.path.exists(CONVERSION_RECORDS_FILE):
        with open(CONVERSION_RECORDS_FILE, "r", encoding="utf-8") as f:
            conversion_records_data = json.load(f)
    else:
        # 如果文件不存在，初始化为空数组并保存
        conversion_records_data = []
        save_conversion_records_data()
    
    if os.path.exists(MODELS_FILE):
        with open(MODELS_FILE, "r", encoding="utf-8") as f:
            models_data = json.load(f)
    else:
        # 如果文件不存在，初始化为空数组并保存
        models_data = []
        save_models_data()

# 保存数据
def save_prompts_data():
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts_data, f, ensure_ascii=False, indent=2)

def save_conversion_records_data():
    with open(CONVERSION_RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(conversion_records_data, f, ensure_ascii=False, indent=2)

def save_models_data():
    with open(MODELS_FILE, "w", encoding="utf-8") as f:
        json.dump(models_data, f, ensure_ascii=False, indent=2)

# EvalScope 数据模型
class EvalScopeTestParams(BaseModel):
    model_name: str = Field(..., alias='modelName')
    api_base_url: str = Field(..., alias='apiBaseUrl')
    api_key: str = Field(..., alias='apiKey')
    concurrency: int = Field(5, alias='concurrency')
    total_requests: int = Field(100, alias='totalRequests')
    input_tokens: int = Field(1000, alias='inputTokens')
    output_tokens: int = Field(500, alias='outputTokens')
    prompt_template: str = Field("default", alias='promptTemplate')
    use_cache: bool = Field(False, alias='useCache')

    class Config:
        populate_by_name = True

class EvalScopeTestResult(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    throughput: float
    total_time: float
    details: List[Dict[str, Any]]

# 数据模型
class Prompt(BaseModel):
    id: int
    title: str
    content: str
    createTime: str

class ConversionRecord(BaseModel):
    id: int
    csvFileName: str
    jsonlFileName: str
    conversionTime: str

class FieldMapping(BaseModel):
    jsonlField: str
    mappingType: str
    selectedColumn: str = None
    multipleMapping: str = None
    customText: str = None
    filterType: str = 'any'
    filterValue: str = ''

class MappingConfig(BaseModel):
    csvFileName: str
    fields: list[FieldMapping]

# 模型数据模型
class Model(BaseModel):
    id: int
    name: str
    description: str
    customHeader: str  # JSON格式的字符串
    url: str
    otherParams: str
    apiKey: str

# 任务跑批相关数据模型
class FieldConfig(BaseModel):
    colName: str
    sourceType: str = "file"  # 默认且唯一支持的类型是file
    selectedFile: str = ""
    selectedField: str = ""
    fileFields: List[str] = []

class BatchTaskConfig(BaseModel):
    promptId: int
    modelId: int
    fieldConfigs: List[FieldConfig]
    taskDescription: str
    progressFile: str = None  # 可选的进度文件名

# 模拟数据存储
# 初始化为空列表，实际数据将从文件加载
prompts_data = []
conversion_records_data = []
models_data = []

# 初始化加载数据
load_data()

# EvalScope 辅助函数
def generate_random_string(length: int = 10) -> str:
    """生成随机字符串作为请求ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_prompt(template_type: str, input_tokens: int) -> str:
    """根据模板类型生成指定长度的提示词"""
    if template_type == "code":
        prompt = "# 编写一个Python函数，实现以下功能:\n" + " " * (input_tokens - 30)
    elif template_type == "summary":
        prompt = "# 总结以下文章内容:\n" + " " * (input_tokens - 20)
    else:  # default
        prompt = "你好，" + " " * (input_tokens - 2)
    # 确保提示词长度接近指定的input_tokens
    return prompt[:input_tokens]


async def send_model_request(params: Dict[str, Any]) -> Dict[str, Any]:
    """发送模型请求并返回结果"""
    request_id = params.get("request_id", generate_random_string())
    model_name = params.get("model_name")
    api_base_url = params.get("api_base_url")
    api_key = params.get("api_key")
    prompt = params.get("prompt")
    input_tokens = params.get("input_tokens")
    output_tokens = params.get("output_tokens")
    use_cache = params.get("use_cache", False)

    # 查找模型配置
    model_config = next((m for m in models_data if m["name"] == model_name), None)
    if not model_config:
        return {
            "request_id": request_id,
            "status": "failed",
            "response_time": 0,
            "input_tokens": input_tokens,
            "output_tokens": 0,
            "total_tokens": input_tokens,
            "error_message": f"未找到模型配置: {model_name}"
        }

    start_time = time.time()
    try:
        # 构建API请求头
        headers = {"Content-Type": "application/json"}
        
        # 记录API密钥和模型配置
        print(f"使用的API密钥: {api_key}")
        print(f"模型配置: {model_config}")
        
        # 处理自定义头
        custom_headers = {}
        if model_config.get("customHeader"):
            try:
                custom_headers = json.loads(model_config["customHeader"])
                # 替换$apiKey变量
                for key, value in custom_headers.items():
                    if isinstance(value, str) and "$apiKey" in value:
                        custom_headers[key] = value.replace("$apiKey", api_key)
                        print(f"替换$apiKey后的{key}头: {custom_headers[key]}")
            except json.JSONDecodeError:
                return {
                    "request_id": request_id,
                    "status": "failed",
                    "response_time": 0,
                    "input_tokens": input_tokens,
                    "output_tokens": 0,
                    "total_tokens": input_tokens,
                    "error_message": f"模型{model_name}的customHeader不是有效的JSON"
                }
        
        # 无论是否有自定义头，都确保Authorization使用Bearer格式
        headers.update(custom_headers)
        auth_header = headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            # 如果没有Bearer前缀，则添加
            if auth_header:
                headers["Authorization"] = f"Bearer {auth_header}"
            else:
                headers["Authorization"] = f"Bearer {api_key}"
        
        print(f"最终使用的Authorization头: {headers['Authorization']}")
        print(f"完整请求头: {headers}")

        # 根据不同的API格式调整请求体
        if "openai" in api_base_url.lower() or "anthropic" in api_base_url.lower() or "siliconflow" in api_base_url.lower():
            # OpenAI、Anthropic或SiliconFlow风格的API
            data = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": output_tokens,
                "temperature": 0.01
            }
        else:
            # 通用格式
            data = {
                "model": model_name,
                "prompt": prompt,
                "max_tokens": output_tokens,
                "temperature": 0.01
            }

        # 添加模型配置中的其他参数
        if model_config.get("otherParams"):
            try:
                other_params = json.loads(model_config["otherParams"])
                data.update(other_params)
            except json.JSONDecodeError:
                return {
                    "request_id": request_id,
                    "status": "failed",
                    "response_time": 0,
                    "input_tokens": input_tokens,
                    "output_tokens": 0,
                    "total_tokens": input_tokens,
                    "error_message": f"模型{model_name}的otherParams不是有效的JSON"
                }

        # 添加缓存控制参数
        if use_cache:
            data["cache_control"] = {"max_age": 3600}

        # 记录请求信息用于调试
        print(f"发送请求到: {api_base_url}")
        print(f"请求头: {headers}")
        print(f"Authorization头: {headers.get('Authorization')}")
        print(f"请求体: {data}")

        # 发送请求（带重试机制）
        max_retries = 2
        retry_count = 0
        async with httpx.AsyncClient() as client:
            while retry_count <= max_retries:
                try:
                    response = await client.post(
                        api_base_url, headers=headers, json=data, timeout=300.0
                    )
                    print(f"响应状态码: {response.status_code}")
                    response.raise_for_status()
                    result = response.json()
                    print(f"响应结果: {result}")
                    break  # 成功，跳出循环
                except httpx.HTTPStatusError as e:
                    print(f"HTTP错误状态码: {e.response.status_code}")
                    print(f"错误响应内容: {e.response.text}")
                    
                    # 处理502错误
                    if e.response.status_code == 502:
                        error_message = f"服务器错误 '502 Bad Gateway' 对于URL '{api_base_url}'"
                        print(f"502错误详情: {e.response.text}")
                        print(f"Authorization头: {headers.get('Authorization')}")
                        if retry_count < max_retries:
                            retry_count += 1
                            print(f"502错误，第 {retry_count} 次重试...")
                            await asyncio.sleep(1)  # 等待1秒后重试
                            continue
                        return {
                            "request_id": request_id,
                            "status": "failed",
                            "response_time": (time.time() - start_time) * 1000,
                            "input_tokens": input_tokens,
                            "output_tokens": 0,
                            "total_tokens": input_tokens,
                            "error_message": f"{error_message}. 请检查API密钥和服务器状态。"
                        }
                    
                    # 处理422错误
                    elif e.response.status_code == 422:
                        error_detail = e.response.text
                        try:
                            error_json = e.response.json()
                            error_detail = str(error_json)
                        except:
                            pass
                        return {
                            "request_id": request_id,
                            "status": "failed",
                            "response_time": (time.time() - start_time) * 1000,
                            "input_tokens": input_tokens,
                            "output_tokens": 0,
                            "total_tokens": input_tokens,
                            "error_message": f"请求格式错误 (422): {error_detail}"
                        }
                    
                    # 其他HTTP错误
                    raise
                except Exception as e:
                    if retry_count < max_retries:
                        retry_count += 1
                        print(f"请求异常，第 {retry_count} 次重试...")
                        await asyncio.sleep(1)  # 等待1秒后重试
                        continue
                    raise

        # 解析响应
        if "choices" in result and len(result["choices"]) > 0:
            if "message" in result["choices"][0]:
                content = result["choices"][0]["message"].get("content", "")
            else:
                content = result["choices"][0].get("text", "")
        else:
            content = "模型返回格式不正确"

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒

        return {
            "request_id": request_id,
            "status": "success",
            "response_time": round(response_time, 2),
            "input_tokens": input_tokens,
            "output_tokens": len(content),
            "total_tokens": input_tokens + len(content),
            "error_message": ""
        }
    except Exception as e:
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒

        return {
            "request_id": request_id,
            "status": "failed",
            "response_time": round(response_time, 2),
            "input_tokens": input_tokens,
            "output_tokens": 0,
            "total_tokens": input_tokens,
            "error_message": str(e)
        }


async def run_concurrent_tests(params: EvalScopeTestParams) -> EvalScopeTestResult:
    """运行并发测试并返回结果"""
    total_requests = params.total_requests
    concurrency = min(params.concurrency, total_requests)

    # 准备请求参数
    request_params = []
    for i in range(total_requests):
        prompt = generate_prompt(params.prompt_template, params.input_tokens)
        request_params.append({
            "request_id": f"req_{i}_{generate_random_string()}",
            "model_name": params.model_name,
            "api_base_url": params.api_base_url,
            "api_key": params.api_key,
            "prompt": prompt,
            "input_tokens": params.input_tokens,
            "output_tokens": params.output_tokens,
            "use_cache": params.use_cache
        })

    # 运行并发请求
    start_time = time.time()
    results = []

    # 使用asyncio.gather进行并发处理
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_send_request(param):
        async with semaphore:
            return await send_model_request(param)

    tasks = [bounded_send_request(param) for param in request_params]
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    total_time = end_time - start_time

    # 统计结果
    successful_requests = sum(1 for r in results if r["status"] == "success")
    failed_requests = total_requests - successful_requests

    # 计算平均响应时间（仅考虑成功的请求）
    successful_response_times = [r["response_time"] for r in results if r["status"] == "success"]
    avg_response_time = sum(successful_response_times) / len(successful_response_times) if successful_response_times else 0

    # 计算吞吐量
    throughput = successful_requests / total_time if total_time > 0 else 0

    return EvalScopeTestResult(
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        avg_response_time=round(avg_response_time, 2),
        throughput=round(throughput, 2),
        total_time=round(total_time, 2),
        details=results
    )

# API路由
@app.get("/")
def read_root():
    return {"message": "大模型数据处理系统后端API"}

# NGINX日志解析相关API

# 定义NGINX日志正则表达式
NGINX_LOG_PATTERN = re.compile(
    r'(?P<remote_addr>\S+)\s+-\s+(?P<remote_user>\S+)\s+\[(?P<time_local>[^\]]+)\]\s+'
    r'"(?P<request>[^"]+)"\s+(?P<status>\d+)\s+(?P<body_bytes_sent>\d+)\s+'
    r'"(?P<http_referer>[^"]*)"\s+"(?P<http_user_agent>[^"]*)"\s+'
    r'"(?P<http_agent_id>[^"]*)"\s+(?P<request_length>\d+)\s+"(?P<upstream_ip>[^"]+)"'
)

def parse_nginx_log_line(line: str) -> Dict[str, Any]:
    """解析单行NGINX日志"""
    match = NGINX_LOG_PATTERN.match(line.strip())
    if match:
        return match.groupdict()
    return {}

@app.post("/api/parse-nginx-log")
async def parse_nginx_log(file: UploadFile = File(...)):
    """解析上传的NGINX日志文件并保存为CSV格式"""
    try:
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"nginx_log_{timestamp}.log"
        csv_filename = f"nginx_log_{timestamp}.csv"
        
        # 保存上传的日志文件
        log_file_path = os.path.join(NGINX_LOGS_DIR, log_filename)
        with open(log_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 解析日志并写入CSV文件
        csv_file_path = os.path.join(NGINX_LOGS_DIR, csv_filename)
        parsed_data = []
        
        with open(log_file_path, "r", encoding="utf-8", errors="ignore") as log_file:
            for line in log_file:
                parsed_line = parse_nginx_log_line(line)
                if parsed_line:
                    parsed_data.append(parsed_line)
        
        # 写入CSV文件
        if parsed_data:
            fieldnames = [
                'remote_addr', 'remote_user', 'time_local', 'request', 
                'status', 'body_bytes_sent', 'http_referer', 'http_user_agent',
                'http_agent_id', 'request_length', 'upstream_ip'
            ]
            
            with open(csv_file_path, "w", encoding="utf-8", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(parsed_data)
        
        return {
            "message": "日志解析完成",
            "downloadUrl": f"/api/download-nginx-csv/{csv_filename}",
            "fileName": csv_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"日志解析失败: {str(e)}")

@app.get("/api/download-nginx-csv/{file_name}")
def download_nginx_csv(file_name: str):
    """下载解析后的CSV文件"""
    try:
        # 验证文件名格式
        if not file_name.startswith("nginx_log_") or not file_name.endswith(".csv"):
            raise HTTPException(status_code=400, detail="无效的文件名")
        
        # 构建文件路径
        file_path = os.path.join(NGINX_LOGS_DIR, file_name)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 返回文件响应
        return FileResponse(file_path, media_type='text/csv', filename=file_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")

@app.post("/api/parse-nginx-log-summary")
async def parse_nginx_log_summary(file: UploadFile = File(...)):
    """解析上传的NGINX日志文件并生成按agent_id汇总的CSV格式"""
    try:
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"nginx_log_{timestamp}.log"
        csv_filename = f"nginx_log_summary_{timestamp}.csv"
        
        # 保存上传的日志文件
        log_file_path = os.path.join(NGINX_LOGS_DIR, log_filename)
        with open(log_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 解析日志并处理数据
        parsed_data = []
        
        with open(log_file_path, "r", encoding="utf-8", errors="ignore") as log_file:
            for line in log_file:
                parsed_line = parse_nginx_log_line(line)
                if parsed_line:
                    parsed_data.append(parsed_line)
        
        # 处理数据：按agent_id汇总最近2天每小时请求数量及平均request_length
        if parsed_data:
            # 转换为DataFrame以便处理
            df = pd.DataFrame(parsed_data)
            
            # 转换time_local为datetime对象
            # NGINX日志时间格式: 27/Jun/2024:14:59:42 +0800
            df['time_local'] = pd.to_datetime(df['time_local'], format='%d/%b/%Y:%H:%M:%S %z', errors='coerce')
            
            # 过滤最近2天的数据
            current_time = datetime.now().astimezone()
            two_days_ago = current_time - pd.Timedelta(days=2)
            df = df[df['time_local'] >= two_days_ago]
            
            # 提取小时信息
            df['hour'] = df['time_local'].dt.floor('H')
            
            # 转换request_length为数值
            df['request_length'] = pd.to_numeric(df['request_length'], errors='coerce')
            
            # 按agent_id和小时分组，计算请求数量和平均request_length
            summary = df.groupby(['http_agent_id', 'hour']).agg({
                'request': 'count',  # 请求数量
                'request_length': 'mean'  # 平均request_length
            }).reset_index()
            
            # 重命名列
            summary.rename(columns={
                'request': 'request_count',
                'request_length': 'avg_request_length'
            }, inplace=True)
            
            # 保存为CSV文件
            csv_file_path = os.path.join(NGINX_LOGS_DIR, csv_filename)
            summary.to_csv(csv_file_path, index=False, encoding='utf-8')
            
            return {
                "message": "日志汇总完成",
                "downloadUrl": f"/api/download-nginx-csv/{csv_filename}",
                "fileName": csv_filename
            }
        else:
            raise HTTPException(status_code=400, detail="无法解析日志文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"日志汇总失败: {str(e)}")

# 上传CSV文件
@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        # 保存文件
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 读取CSV文件的列名
        df = pd.read_csv(file_path)
        columns = df.columns.tolist()
        
        return {"filename": file.filename, "columns": columns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

# 获取提示词列表
@app.get("/api/prompts", response_model=List[Prompt])
def get_prompts():
    return prompts_data

# 添加新提示词
@app.post("/api/prompts")
def add_prompt(prompt: Prompt):
    # 检查ID是否已存在
    for existing_prompt in prompts_data:
        if existing_prompt["id"] == prompt.id:
            raise HTTPException(status_code=400, detail="提示词ID已存在")
    
    prompts_data.append(prompt.dict())
    save_prompts_data()
    return {"message": "提示词添加成功"}

# 更新提示词
@app.put("/api/prompts/{prompt_id}")
def update_prompt(prompt_id: int, prompt: Prompt):
    for i, p in enumerate(prompts_data):
        if p["id"] == prompt_id:
            prompts_data[i] = prompt.dict()
            save_prompts_data()
            return {"message": "提示词更新成功"}
    raise HTTPException(status_code=404, detail="提示词未找到")

# 删除提示词
@app.delete("/api/prompts/{prompt_id}")
def delete_prompt(prompt_id: int):
    for i, p in enumerate(prompts_data):
        if p["id"] == prompt_id:
            del prompts_data[i]
            save_prompts_data()
            return {"message": "提示词删除成功"}
    raise HTTPException(status_code=404, detail="提示词未找到")

# 任务跑批相关API
@app.get("/api/jsonl-files")
def get_jsonl_files():
    """获取所有JSONL文件列表"""
    try:
        input_data_dir = os.path.join(DATA_DIR, 'input_data')
        files = [f for f in os.listdir(input_data_dir) if f.endswith('.jsonl')] if os.path.exists(input_data_dir) else []
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@app.get("/api/jsonl-files/{file_name}/fields")
def get_jsonl_file_fields(file_name: str):
    """获取指定JSONL文件的字段列表"""
    try:
        # 检查文件是否存在
        file_path = os.path.join(DATA_DIR, 'input_data', file_name)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件未找到")
        
        # 检查文件扩展名
        if not file_name.endswith('.jsonl'):
            raise HTTPException(status_code=400, detail="文件格式不正确")
        
        # 读取文件的第一行来获取字段
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if not first_line:
                return {"fields": []}
            
            # 解析JSON
            data = json.loads(first_line)
            fields = list(data.keys())
            
            return {"fields": fields}
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"文件格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件字段列表失败: {str(e)}")

@app.post("/api/batch-task")
async def execute_batch_task(config: BatchTaskConfig):
    """执行批量任务"""

    print("execute_batch_task",config)
    try:
        import jsonlines
        
        # 获取提示词
        prompt = next((p for p in prompts_data if p["id"] == config.promptId), None)
        if not prompt:
            raise HTTPException(status_code=404, detail="提示词未找到")
        
        # 获取模型配置
        model = next((m for m in models_data if m["id"] == config.modelId), None)
        if not model:
            raise HTTPException(status_code=404, detail="模型未找到")

        print("prompt",prompt)
        print("model",model)
        
        # 处理字段映射和数据读取逻辑
        # 收集所有需要的数据源
        data_sources = {}
        
        # 处理每个字段配置
        for field_config in config.fieldConfigs:
            # 检查selectedFile是否为空
            if not field_config.selectedFile:
                raise HTTPException(status_code=400, detail="请选择JSONL文件")
            
            # 从JSONL文件读取
            file_path = os.path.join(DATA_DIR, 'input_data', field_config.selectedFile)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"文件 {field_config.selectedFile} 未找到")
            
            # 读取JSONL文件的所有记录
            records = []
            with jsonlines.open(file_path) as reader:
                for item in reader:
                    records.append(item)
            
            # 使用selectedField作为键，而不是colName
            data_sources[field_config.selectedField] = {
                "type": "file",
                "records": records,
                "field": field_config.selectedField
            }
        
        # 生成提示词内容并调用大模型API
        results = []
        record_count = 0
        request_details = []  # 用于存储请求详情
        
        # 使用前端传递的进度文件名，或者生成一个新的
        if config.progressFile:
            progress_file = config.progressFile
        else:
            progress_file = f"progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(8).hex()}.log"
        progress_path = os.path.join(DATA_DIR, 'progress_logs', progress_file)
        
        # 确保进度日志目录存在
        progress_logs_dir = os.path.join(DATA_DIR, 'progress_logs')
        if not os.path.exists(progress_logs_dir):
            os.makedirs(progress_logs_dir)
        
        # 在任务开始时就返回进度文件名
        # 先创建一个空的进度文件
        with open(progress_path, 'w', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务开始执行\n")
        
        # 启动一个后台任务来执行实际的批量处理
        background_task = asyncio.create_task(_execute_batch_task_background(
            config, prompt, model, data_sources, progress_path, progress_file
        ))
        
        # 立即返回进度文件名，让前端可以开始轮询
        return {
            "progressFile": progress_file
        }
    
    finally:
        pass
# 后台执行批量任务的函数
async def _execute_batch_task_background(config, prompt, model, data_sources, progress_path, progress_file):
    """在后台执行批量任务"""
    try:
        
        # 生成提示词内容并调用大模型API
        results = []
        record_count = 0
        request_details = []  # 用于存储请求详情
        
        # 简单示例：假设我们只处理第一个数据源的所有记录
        # 在实际应用中，您需要根据业务逻辑来组合多个数据源
        primary_source = next(iter(data_sources.values()), None) if data_sources else None
        
        if primary_source and primary_source["type"] == "file":
            record_count = len(primary_source["records"])
            for i, record in enumerate(primary_source["records"]):
                # 构建提示词内容
                prompt_content = config.taskDescription
                
                # 处理特殊字符 <dateTime>
                current_date = datetime.now()
                date_str = f"{current_date.year}年{current_date.month}月{current_date.day}日"
                prompt_content = prompt_content.replace("<dateTime>", date_str)
                
                # 替换映射名称占位符
                for field_name, source_info in data_sources.items():
                    if source_info["type"] == "file":
                        field_value = record.get(source_info["field"], "")
                    
                    prompt_content = prompt_content.replace(f"{{{field_name}}}", str(field_value))
                
                # 构建API请求参数
                api_params = {
                    "model": model["name"],
                    "messages": [
                        {
                            "role": "system",
                            "content": prompt["content"]
                        },
                        {
                            "role": "user",
                            "content": prompt_content
                        }
                    ],
                    "temperature": 0.01,
                    "stream": False
                }
                
                # 添加模型的其他参数
                if model.get("otherParams"):
                    try:
                        other_params = json.loads(model["otherParams"])
                        api_params.update(other_params)
                    except json.JSONDecodeError:
                        pass  # 如果解析失败，忽略otherParams
                
                # 设置请求头
                headers = {
                    "Content-Type": "application/json"
                }
                
                # 添加模型的自定义请求头
                if model.get("customHeader"):
                    try:
                        custom_headers = json.loads(model["customHeader"])
                        headers.update(custom_headers)
                    except json.JSONDecodeError:
                        print("自定义请求头格式错误")
                        pass  # 如果解析失败，忽略customHeader
                
                # 记录请求详情
                request_details.append({
                    "url": model["url"],
                    "headers": headers,
                    "params": api_params
                })

                # 写入进度日志
                with open(progress_path, 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始处理第 {i+1} 条记录\n")
                    f.write(f"提示词内容: {prompt_content[:100]}...\n")

                
                # 发送POST请求到大模型API
                # try:
                print("批量请求开始:"+str(i))

                response = httpx.post(
                    model["url"],
                    headers=headers,
                    json=api_params,
                    timeout=300.0  # 设置30秒超时
                )
                response.raise_for_status()  # 检查HTTP错误
                result_data = response.json()
                
                # 提取模型响应内容
                if "choices" in result_data and len(result_data["choices"]) > 0:
                    message = result_data["choices"][0]["message"]
                    # 如果存在reasoning_content字段，则将其作为回答的一部分
                    if "reasoning_content" in message and message["reasoning_content"] is not None:
                        model_response = "<think>" + message["reasoning_content"] + "</think>"
                    else:
                        model_response = ""
                    # 提取content字段作为主要响应
                    model_response += " " + message.get("content", "")

                else:
                    model_response = "模型返回格式不正确"

                print("批量请求完成:"+str(i))
                
                # 写入成功响应的进度日志
                with open(progress_path, 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 第 {i+1} 条记录处理成功\n")
                    f.write(f"模型响应: {model_response[:100]}...\n\n")
                # except Exception as e:
                #     # 如果API调用失败，使用模拟响应
                #     model_response = f"API调用失败: {str(e)}"
                #     print("批量请求报错:"+model_response)

                    
                    # 写入失败的进度日志
                    # with open(progress_path, 'a', encoding='utf-8') as f:
                    #     f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 第 {i+1} 条记录处理失败: {str(e)}\n\n")
                
                results.append({
                    "input": prompt_content,
                    "output": model_response
                })
                
                # 在请求之间添加间隔（1秒）
                if i < len(primary_source["records"]) - 1:  # 不在最后一个请求后添加间隔
                    await asyncio.sleep(10)
        
        # 保存结果到文件 (CSV格式)
        result_file = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        batch_results_dir = os.path.join(DATA_DIR, 'batch_results')
        if not os.path.exists(batch_results_dir):
            os.makedirs(batch_results_dir)
        result_path = os.path.join(batch_results_dir, result_file)
        
        # 写入CSV文件
        with open(result_path, mode='w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['system_prompt', 'task_description', 'reasoning_content', 'content']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                # 提取各个字段
                system_prompt = prompt["content"]
                task_description = prompt_content
                
                # 从result["output"]中分离reasoning_content和content
                output = result["output"]
                reasoning_content = ""
                content = output
                
                # 检查是否有<think>标签
                if "<think>" in output and "</think>" in output:
                    # 提取reasoning_content
                    start = output.find("<think>") + len("<think>")
                    end = output.find("</think>")
                    reasoning_content = output[start:end]
                    # 提取content (去除<think>部分)
                    content = output[end + len("</think>"):].strip()
                
                writer.writerow({
                    'system_prompt': system_prompt,
                    'task_description': task_description,
                    'reasoning_content': reasoning_content,
                    'content': content
                })
        
        # 写入任务完成的进度日志
        with open(progress_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务执行完成，共处理{record_count}条记录\n")
        
        return {
            "message": "任务执行成功",
            "resultFile": result_file,
            "recordCount": record_count,
            "requestCount": len(results)
        }
    except Exception as e:
        # 写入任务失败的进度日志
        with open(progress_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务执行失败: {str(e)}\n")
        
        print(f"执行批量任务时发生错误: {str(e)}")
        raise e

# 获取所有模型
@app.get("/api/models", response_model=List[Model])
def get_models():
    return models_data

# 添加模型
@app.post("/api/models")
def add_model(model: Model):
    # 检查ID是否已存在
    for existing_model in models_data:
        if existing_model["id"] == model.id:
            raise HTTPException(status_code=400, detail="模型ID已存在")
    
    # 验证customHeader是否为有效的JSON字符串
    try:
        if model.customHeader:
            json.loads(model.customHeader)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="customHeader必须是有效的JSON字符串")
    
    # 验证otherParams是否为有效的JSON字符串
    try:
        if model.otherParams:
            json.loads(model.otherParams)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="otherParams必须是有效的JSON字符串")
    
    models_data.append(model.dict())
    save_models_data()
    return {"message": "模型添加成功"}

# 更新模型
@app.put("/api/models/{model_id}")
def update_model(model_id: int, model: Model):
    for i, m in enumerate(models_data):
        if m["id"] == model_id:
            models_data[i] = model.dict()
            save_models_data()
            return {"message": "模型更新成功"}
    raise HTTPException(status_code=404, detail="模型未找到")

# 删除模型
@app.delete("/api/models/{model_id}")
def delete_model(model_id: int):
    for i, m in enumerate(models_data):
        if m["id"] == model_id:
            del models_data[i]
            save_models_data()
            return {"message": "模型删除成功"}
    raise HTTPException(status_code=404, detail="模型未找到")

# 获取进度日志内容
@app.get("/api/progress/{progress_file}")
def get_progress(progress_file: str, last_position: int = 0):
    # 构建正确的进度文件路径
    progress_logs_dir = os.path.join(DATA_DIR, 'progress_logs')
    progress_path = os.path.join(progress_logs_dir, progress_file)
    if not os.path.exists(progress_path):
        raise HTTPException(status_code=404, detail="进度文件未找到")
    
    try:
        # 如果last_position为0，返回整个文件内容
        if last_position == 0:
            with open(progress_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content, "position": len(content)}
        else:
            # 只返回从last_position开始的新内容
            with open(progress_path, 'r', encoding='utf-8') as f:
                f.seek(last_position)
                new_content = f.read()
            return {"content": new_content, "position": last_position + len(new_content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取进度文件失败: {str(e)}")

# 获取跑批结果列表（支持分页）
@app.get("/api/batch-results")
def get_batch_results(page: int = 1, pageSize: int = 20):
    try:
        # 查找所有output_*.csv文件
        batch_results_dir = os.path.join(DATA_DIR, 'batch_results')
        pattern = os.path.join(batch_results_dir, "output_*.csv")
        files = glob.glob(pattern)
        
        # 提取文件名和修改时间
        results = []
        for file_path in files:
            file_name = os.path.basename(file_path)
            mod_time = os.path.getmtime(file_path)
            results.append({
                "fileName": file_name,
                "modTime": mod_time
            })
        
        # 按修改时间倒序排序
        results.sort(key=lambda x: x["modTime"], reverse=True)
        
        # 分页处理
        total = len(results)
        start_index = (page - 1) * pageSize
        end_index = start_index + pageSize
        paginated_results = results[start_index:end_index]
        
        return {
            "results": paginated_results,
            "total": total,
            "page": page,
            "pageSize": pageSize
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取跑批结果列表失败: {str(e)}")

# 获取特定跑批结果文件内容
@app.get("/api/batch-results/{file_name}")
def get_batch_result_content(file_name: str):
    try:
        # 验证文件名格式
        if not file_name.startswith("output_") or not file_name.endswith(".csv"):
            raise HTTPException(status_code=400, detail="无效的文件名")
        
        # 构建文件路径
        batch_results_dir = os.path.join(DATA_DIR, 'batch_results')
        file_path = os.path.join(batch_results_dir, file_name)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取CSV文件内容
        results = []
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for item in reader:
                results.append(item)
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取跑批结果内容失败: {str(e)}")

# EvalScope API
@app.post("/api/evalscope/run")
async def run_evalscope_test(params: EvalScopeTestParams):
    """运行模型性能测试"""
    try:
        # 使用全局配置的logger
        logger = logging.getLogger("evalscope")
        logger.setLevel(logging.DEBUG)  # 确保日志级别为DEBUG

        # 记录请求参数用于调试
        logger.debug(f"接收到evalscope测试请求: {params.dict()}")
        logger.debug(f"模型名称: {params.model_name}")
        logger.debug(f"并发数: {params.concurrency}")
        logger.debug(f"请求总数: {params.total_requests}")
        logger.debug(f"输入令牌数: {params.input_tokens}")
        logger.debug(f"输出令牌数: {params.output_tokens}")
        logger.debug(f"API基础URL: {params.api_base_url}")
        logger.debug(f"API密钥: {params.api_key}")
        
        # 验证参数
        if not params.model_name:
            logger.error(f"422错误: 模型名称不能为空 (model_name: {params.model_name})")
            raise HTTPException(status_code=422, detail="模型名称不能为空")
        if params.concurrency <= 0 or params.total_requests <= 0:
            logger.error(f"422错误: 并发数({params.concurrency})和请求总数({params.total_requests})必须大于0")
            raise HTTPException(status_code=422, detail="并发数和请求总数必须大于0")
        if params.input_tokens <= 0 or params.output_tokens <= 0:
            logger.error(f"422错误: 输入令牌数({params.input_tokens})和输出令牌数({params.output_tokens})必须大于0")
            raise HTTPException(status_code=422, detail="输入令牌数和输出令牌数必须大于0")
        if not params.api_base_url:
            logger.error(f"422错误: API基础URL不能为空 (api_base_url: {params.api_base_url})")
            raise HTTPException(status_code=422, detail="API基础URL不能为空")
        if not params.api_key:
            logger.error(f"422错误: API密钥不能为空 (api_key: {params.api_key})")
            raise HTTPException(status_code=422, detail="API密钥不能为空")

        # 运行测试
        result = await run_concurrent_tests(params)

        return {
            "success": True,
            "results": result.dict()
        }
    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"测试出错: {str(e)}"
        }

# 下载跑批结果文件
@app.get("/api/download-batch-result/{file_name}")
def download_batch_result(file_name: str):
    try:
        # 验证文件名格式
        if not file_name.startswith("output_") or not file_name.endswith(".csv"):
            raise HTTPException(status_code=400, detail="无效的文件名")
        
        # 构建文件路径
        batch_results_dir = os.path.join(DATA_DIR, 'batch_results')
        file_path = os.path.join(batch_results_dir, file_name)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 返回文件响应
        return FileResponse(file_path, media_type='text/csv', filename=file_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载跑批结果文件失败: {str(e)}")

# 删除跑批结果文件
@app.delete("/api/batch-results/{file_name}")
def delete_batch_result(file_name: str):
    try:
        # 验证文件名格式
        if not file_name.startswith("output_") or not file_name.endswith(".jsonl"):
            raise HTTPException(status_code=400, detail="无效的文件名")
        
        # 构建文件路径
        batch_results_dir = os.path.join(DATA_DIR, 'batch_results')
        file_path = os.path.join(batch_results_dir, file_name)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除文件
        os.remove(file_path)
        
        return {"message": "文件删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除跑批结果文件失败: {str(e)}")

# 获取转换记录列表
@app.get("/api/conversion-records", response_model=List[ConversionRecord])
def get_conversion_records():
    return conversion_records_data

# 导出JSONL文件
@app.post("/api/export-jsonl")
def export_jsonl(mapping_config: MappingConfig):
    try:
        # 获取CSV文件路径
        csv_filename = mapping_config.csvFileName
        if not csv_filename:
            raise HTTPException(status_code=400, detail="CSV文件名不能为空")
        
        csv_path = os.path.join(DATA_DIR, csv_filename)
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="CSV文件不存在")
        
        # 读取CSV文件
        df = pd.read_csv(csv_path)
        
        # 根据映射配置生成JSONL数据
        jsonl_data = []
        for _, row in df.iterrows():
            valid_row = True
            jsonl_item = {}
            
            # 先检查所有筛选条件
            for field_config in mapping_config.fields:
                if field_config.mappingType == "single" and field_config.filterType != 'any':
                    selected_column = field_config.selectedColumn
                    if selected_column not in df.columns:
                        continue
                    
                    cell_value = row[selected_column]
                    filter_type = field_config.filterType
                    filter_value = field_config.filterValue
                    
                    # 应用筛选条件
                    if filter_type == 'not_empty':
                        if pd.isna(cell_value) or cell_value == '':
                            valid_row = False
                            break
                    elif filter_type == 'equals':
                        if str(cell_value) != str(filter_value):
                            valid_row = False
                            break
                    elif filter_type == 'greater_than':
                        try:
                            if float(cell_value) <= float(filter_value):
                                valid_row = False
                                break
                        except (ValueError, TypeError):
                            valid_row = False
                            break
                    elif filter_type == 'less_than':
                        try:
                            if float(cell_value) >= float(filter_value):
                                valid_row = False
                                break
                        except (ValueError, TypeError):
                            valid_row = False
                            break
                    elif filter_type == 'greater_or_equal':
                        try:
                            if float(cell_value) < float(filter_value):
                                valid_row = False
                                break
                        except (ValueError, TypeError):
                            valid_row = False
                            break
                    elif filter_type == 'less_or_equal':
                        try:
                            if float(cell_value) > float(filter_value):
                                valid_row = False
                                break
                        except (ValueError, TypeError):
                            valid_row = False
                            break
            
            if not valid_row:
                continue
            
            # 应用字段映射
            for field_config in mapping_config.fields:
                jsonl_field = field_config.jsonlField
                mapping_type = field_config.mappingType
                
                if mapping_type == "single":
                    selected_column = field_config.selectedColumn
                    if selected_column in df.columns:
                        jsonl_item[jsonl_field] = row[selected_column]
                elif mapping_type == "multiple":
                    # 解析表达式
                    multiple_mapping = field_config.multipleMapping or ""
                    if multiple_mapping:
                        # 支持 row['column_name'] + "text" + row['another_column'] 格式
                        try:
                            # 替换 row['column_name'] 为实际值
                            parsed_value = multiple_mapping
                            import re
                            # 查找所有 row['column_name'] 模式
                            matches = re.findall(r"row\['([^']*)'\]", multiple_mapping)
                            for column_name in matches:
                                if column_name in df.columns:
                                    # 替换为实际值，需要转换为字符串
                                    column_value = str(row[column_name])
                                    # 转义特殊字符以避免在eval中出现问题
                                    escaped_column_value = repr(column_value)
                                    parsed_value = parsed_value.replace(f"row['{column_name}']", escaped_column_value)
                            
                            # 使用eval安全地求值表达式
                            # 注意：在生产环境中应该使用更安全的方法，如ast.literal_eval或专用的表达式解析库
                            jsonl_item[jsonl_field] = eval(parsed_value)
                        except Exception as e:
                            # 如果解析失败，使用原始表达式
                            jsonl_item[jsonl_field] = multiple_mapping
                    else:
                        jsonl_item[jsonl_field] = ""
                elif mapping_type == "custom":
                    custom_text = field_config.customText or ""
                    jsonl_item[jsonl_field] = custom_text
            
            jsonl_data.append(jsonl_item)
        
        # 生成JSONL文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 从CSV文件名中移除扩展名
        csv_basename = os.path.splitext(csv_filename)[0]
        jsonl_filename = f"{csv_basename}_exported_{timestamp}.jsonl"
        input_data_dir = os.path.join(DATA_DIR, 'input_data')
        if not os.path.exists(input_data_dir):
            os.makedirs(input_data_dir)
        jsonl_path = os.path.join(input_data_dir, jsonl_filename)
        
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for item in jsonl_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        # 添加转换记录
        conversion_records_data.append({
            "id": len(conversion_records_data) + 1,
            "csvFileName": csv_filename,
            "jsonlFileName": jsonl_filename,
            "conversionTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_conversion_records_data()
        
        return {"filename": jsonl_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

# 下载文件
@app.get("/api/download/{file_name}")
async def download_file(file_name: str):
    # 检查文件是否在 input_data 目录中
    input_data_dir = os.path.join(DATA_DIR, 'input_data')
    file_path = os.path.join(input_data_dir, file_name)
    
    # 如果不在 input_data 目录中，检查是否在 batch_results 目录中
    if not os.path.exists(file_path):
        batch_results_dir = os.path.join(DATA_DIR, 'batch_results')
        file_path = os.path.join(batch_results_dir, file_name)
    
    # 如果仍然找不到文件，检查是否在根目录中
    if not os.path.exists(file_path):
        file_path = os.path.join(DATA_DIR, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件未找到")
    
    return FileResponse(file_path, media_type='application/octet-stream', filename=file_name)

# 更新转换记录文件名
@app.put("/api/conversion-records/{record_id}")
def update_conversion_record(record_id: int, update_data: dict = Body(...)):
    for i, record in enumerate(conversion_records_data):
        if record["id"] == record_id:
            # 更新文件名
            if "csvFileName" in update_data:
                record["csvFileName"] = update_data["csvFileName"]
            if "jsonlFileName" in update_data:
                record["jsonlFileName"] = update_data["jsonlFileName"]
            save_conversion_records_data()
            return {"message": "转换记录更新成功"}
    raise HTTPException(status_code=404, detail="转换记录未找到")

# 删除转换记录
@app.delete("/api/conversion-records/{record_id}")
def delete_conversion_record(record_id: int):
    global conversion_records_data
    for i, record in enumerate(conversion_records_data):
        if record["id"] == record_id:
            # 删除关联的文件
            # CSV文件在 input_data 目录中
            input_data_dir = os.path.join(DATA_DIR, 'input_data')
            csv_file_path = os.path.join(input_data_dir, record["csvFileName"])
            
            # JSONL文件可能在 input_data 或 batch_results 目录中
            # 先检查 input_data 目录
            jsonl_file_path = os.path.join(input_data_dir, record["jsonlFileName"])
            if not os.path.exists(jsonl_file_path):
                # 如果不在 input_data 目录中，检查 batch_results 目录
                batch_results_dir = os.path.join(DATA_DIR, 'batch_results')
                jsonl_file_path = os.path.join(batch_results_dir, record["jsonlFileName"])
            
            # 删除文件（如果存在）
            if os.path.exists(csv_file_path):
                os.remove(csv_file_path)
            if os.path.exists(jsonl_file_path):
                os.remove(jsonl_file_path)
            
            # 删除记录
            del conversion_records_data[i]
            save_conversion_records_data()
            return {"message": "转换记录删除成功"}
    raise HTTPException(status_code=404, detail="转换记录未找到")

if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)


# uvicorn main:app --host 0.0.0.0 --port 8001