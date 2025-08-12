# 数据目录结构说明

## 目录结构

- `models/` - 存放模型配置文件
- `prompts/` - 存放提示词模板文件
- `batch_results/` - 存放批量处理结果文件
- `progress_logs/` - 存放任务进度日志文件
- `input_data/` - 存放原始输入数据文件
- `conversion_records.json` - 文件转换记录

## 文件说明

### models/models.json
存放模型配置信息，包括模型名称、API地址、API密钥等。

### prompts/prompts.json
存放提示词模板，用于批量处理任务。

### batch_results/*.jsonl
存放批量处理的结果文件，每行一个JSON对象。

### progress_logs/*.log
存放批量任务的进度日志，记录任务执行过程中的信息。

### input_data/*.csv
存放原始输入数据文件，用于批量处理任务。

### conversion_records.json
记录文件转换的历史信息。