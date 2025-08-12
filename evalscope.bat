@echo off

REM 检查Python是否可用
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python。请确保Python已安装并添加到系统PATH中。
    pause
    exit /b 1
)

REM 设置默认参数值
set "parallel=1"
set "number=1"
set "model=DeepSeek-R1"
set "url=http://175.102.135.20/h20_dsr1/v1/chat/completions"
set "headers=Authorization=Bearer kL9jvQaXp2EwNmZb67Rt"
set "api=openai"
set "dataset=random"
set "max_tokens=1111"
set "min_tokens=1111"
set "prefix_length=0"
set "tokenizer_path=%~dp0"
set "min_prompt_length=2222"
set "max_prompt_length=2222"
set "extra_args={"ignore_eos": true}"

REM 处理命令行参数
if "%1"=="perf" (
    shift
    :parse_perf_args
    if "%1"=="--parallel" (
        set "parallel=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--number" (
        set "number=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--model" (
        set "model=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--url" (
        set "url=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--headers" (
        set "headers=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--api" (
        set "api=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--dataset" (
        set "dataset=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--max-tokens" (
        set "max_tokens=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--min-tokens" (
        set "min_tokens=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--prefix-length" (
        set "prefix_length=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--tokenizer-path" (
        set "tokenizer_path=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--min-prompt-length" (
        set "min_prompt_length=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--max-prompt-length" (
        set "max_prompt_length=%2"
        shift
        shift
        goto parse_perf_args
    )
    if "%1"=="--extra-args" (
        set "extra_args=%2"
        shift
        shift
        goto parse_perf_args
    )

    REM 调用Python脚本
    python "%~dp0evalscope.py" perf ^
        --parallel %parallel% ^
        --number %number% ^
        --model "%model%" ^
        --url "%url%" ^
        --headers "%headers%" ^
        --api %api% ^
        --dataset %dataset% ^
        --max-tokens %max_tokens% ^
        --min-tokens %min_tokens% ^
        --prefix-length %prefix_length% ^
        --tokenizer-path "%tokenizer_path%" ^
        --min-prompt-length %min_prompt_length% ^
        --max-prompt-length %max_prompt_length% ^
        --extra-args "%extra_args%"
) else (
    echo Evalscope 工具使用帮助
    echo.
    echo 用法:
    echo   evalscope perf [选项...]
    echo.
    echo 选项:
    echo   --parallel     并发数 (默认: 1)
    echo   --number       总的运行次数 (默认: 1)
    echo   --model        模型名称 (默认: DeepSeek-R1)
    echo   --url          API URL (默认: http://175.102.135.20/h20_dsr1/v1/chat/completions)
    echo   --headers      请求头 (默认: Authorization=Bearer kL9jvQaXp2EwNmZb67Rt)
    echo   --api          API类型 (默认: openai)
    echo   --dataset      数据集类型 (默认: random)
    echo   --max-tokens   最大tokens (默认: 1111)
    echo   --min-tokens   最小tokens (默认: 1111)
    echo   --prefix-length 前缀长度 (默认: 0)
    echo   --tokenizer-path tokenizer路径 (默认: 当前目录)
    echo   --min-prompt-length 最小提示长度 (默认: 2222)
    echo   --max-prompt-length 最大提示长度 (默认: 2222)
    echo   --extra-args   额外参数 (默认: {"ignore_eos": true})
    echo.
    echo 示例:
    echo   evalscope perf --parallel 1 --number 1 --model DeepSeek-R1 --url "http://175.102.135.20/h20_dsr1/v1/chat/completions" --headers "Authorization=Bearer kL9jvQaXp2EwNmZb67Rt" --api openai --dataset random --max-tokens 1111 --min-tokens 1111 --prefix-length 0 --tokenizer-path "%~dp0" --min-prompt-length 2222 --max-prompt-length 2222 --extra-args '{"ignore_eos": true}'
)

pause