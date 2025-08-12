# EvalScope 模型性能评估工具

EvalScope 是一个用于评估语言模型性能的工具，支持并发测试、自定义提示生成和详细的性能指标统计。

## 功能特点

- 支持并发性能测试
- 自定义提示长度范围
- 详细的性能指标统计（吞吐量、响应时间、生成速度等）
- 支持多种筛选条件
- 兼容OpenAI风格API

## 依赖项

- Python 3.7+
- transformers >= 4.30.0
- requests >= 2.31.0
- torch >= 2.0.0

## 安装

1. 克隆或下载此项目
2. 安装依赖项：
   ```
   pip install -r requirements.txt
   ```

## 使用方法

### Windows用户

使用批处理文件运行：

```
 evalscope perf [选项...]
```

### 示例

```
 evalscope perf --parallel 1 --number 1 --model DeepSeek-R1 --url "http://175.102.135.20/h20_dsr1/v1/chat/completions" --headers "Authorization=Bearer kL9jvQaXp2EwNmZb67Rt" --api openai --dataset random --max-tokens 1111 --min-tokens 1111 --prefix-length 0 --tokenizer-path "./" --min-prompt-length 2222 --max-prompt-length 2222 --extra-args '{"ignore_eos": true}'
```

### 命令行参数

#### 必需参数
- `--model`: 模型名称
- `--url`: API URL
- `--headers`: 请求头，格式: Key1=Value1;Key2=Value2
- `--max-tokens`: 最大tokens
- `--min-tokens`: 最小tokens
- `--tokenizer-path`: tokenizer路径
- `--min-prompt-length`: 最小提示长度
- `--max-prompt-length`: 最大提示长度

#### 可选参数
- `--parallel`: 并发数 (默认: 1)
- `--number`: 总的运行次数 (默认: 1)
- `--api`: API类型 (默认: openai)
- `--dataset`: 数据集类型 (默认: random)
- `--prefix-length`: 前缀长度 (默认: 0)
- `--extra-args`: 额外参数，JSON格式 (默认: {"ignore_eos": true})

## 性能指标

运行测试后，工具会输出以下性能指标：
- 成功/失败次数
- 平均输入/输出/总tokens
- 平均响应时间
- 平均生成速度 (tokens/秒)
- 总耗时
- 吞吐量 (请求/秒)

## 注意事项

1. 确保提供的tokenizer路径包含有效的tokenizer.json和tokenizer_config.json文件
2. 对于大型测试，建议适当增加并发数以提高测试效率
3. 根据模型性能调整max-tokens和min-tokens参数
4. 如遇到PyTorch版本兼容性问题，工具已内置兼容性解决方案