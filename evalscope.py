import argparse
import os
import json
import time
import requests
import threading
import concurrent.futures

# 解决PyTorch版本兼容性问题
try:
    import torch
    # 检查并定义缺少的torch属性
    if not hasattr(torch, 'uint64'):
        torch.uint64 = torch.int64
    if not hasattr(torch, 'uint32'):
        torch.uint32 = torch.int32
    if not hasattr(torch, 'uint16'):
        torch.uint16 = torch.int16
except ImportError:
    print("警告: 未找到PyTorch，某些功能可能无法正常工作")

from transformers import AutoTokenizer

# 加载tokenizer配置
def load_tokenizer(tokenizer_path):
    try:
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        return tokenizer
    except Exception as e:
        print(f"加载tokenizer失败: {e}")
        return None

# 生成随机提示
def generate_random_prompt(tokenizer, min_length, max_length):
    # 这里简化实现，实际应用中可以根据需求生成更复杂的随机提示
    import random
    import string
    prompt_length = random.randint(min_length, max_length)
    prompt = ''.join(random.choices(string.ascii_letters + string.digits, k=prompt_length))
    return prompt

# 调用模型API
def call_model_api(url, headers, model, prompt, max_tokens, min_tokens, ignore_eos=False):
    try:
        headers_dict = {h.split('=')[0]: h.split('=')[1] for h in headers.split(';')}
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "min_tokens": min_tokens,
            "ignore_eos": ignore_eos
        }

        print(f"发送请求到: {url}")
        print(f"请求头: {headers_dict}")
        print(f"请求体: {data}")

        start_time = time.time()
        response = requests.post(url, headers=headers_dict, json=data, timeout=60)
        end_time = time.time()

        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            try:
                result = response.json()
                # 计算token数量和生成速度
                input_tokens = result['usage']['prompt_tokens']
                output_tokens = result['usage']['completion_tokens']
                total_tokens = result['usage']['total_tokens']
                speed = total_tokens / (end_time - start_time)

                return {
                    'success': True,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': total_tokens,
                    'time_taken': end_time - start_time,
                    'speed': speed
                }
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'error': f"API响应不是有效的JSON: {response.text}"
                }
        elif response.status_code == 502:
            # 特别处理502错误，提供更多调试信息
            return {
                'success': False,
                'error': f"API调用失败，状态码: 502 (Bad Gateway)。这通常表示服务器作为网关或代理从上游服务器收到无效响应。\n请求URL: {url}\n请求头: {headers_dict}\n响应内容: {response.text}"
            }
        else:
            return {
                'success': False,
                'error': f"API调用失败，状态码: {response.status_code}, 响应: {response.text}"
            }
    except Exception as e:
        return {
            'success': False,
            'error': f"API调用异常: {str(e)}"
        }

# 运行单次测试
def run_single_test(args, tokenizer):
    prompt = generate_random_prompt(tokenizer, args.min_prompt_length, args.max_prompt_length)
    result = call_model_api(
        url=args.url,
        headers=args.headers,
        model=args.model,
        prompt=prompt,
        max_tokens=args.max_tokens,
        min_tokens=args.min_tokens,
        ignore_eos=args.extra_args.get('ignore_eos', False)
    )
    return result

# 加载模型配置
def load_model_config(model_name):
    try:
        with open('data/models/models.json', 'r', encoding='utf-8') as f:
            models_data = json.load(f)
        return next((m for m in models_data if m['name'] == model_name), None)
    except Exception as e:
        print(f'加载模型配置失败: {e}')
        return None

# 主函数
def main():
    parser = argparse.ArgumentParser(description='EvalScope: 模型性能评估工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # perf子命令
    perf_parser = subparsers.add_parser('perf', help='性能测试')
    perf_parser.add_argument('--parallel', type=int, default=1, help='并发数')
    perf_parser.add_argument('--number', type=int, default=1, help='总的运行次数')
    perf_parser.add_argument('--model', required=True, help='模型名称')
    perf_parser.add_argument('--tokenizer-path', default='.', help='tokenizer路径 (默认: 当前目录)')
    perf_parser.add_argument('--min-prompt-length', type=int, default=100, help='最小提示长度')
    perf_parser.add_argument('--max-prompt-length', type=int, default=200, help='最大提示长度')
    perf_parser.add_argument('--extra-args', type=str, default='{}', help='额外参数，JSON格式')

    args = parser.parse_args()

    # 加载模型配置
    model_config = load_model_config(args.model)
    if not model_config:
        print(f'错误: 未找到模型配置: {args.model}')
        return

    # 从模型配置中设置参数
    args.url = model_config.get('url')
    args.headers = ''
    if model_config.get('customHeader'):
        try:
            headers = json.loads(model_config['customHeader'])
            # 确保Authorization头使用正确的Bearer token格式
            api_key = model_config.get('apiKey', '')
            if api_key and 'Authorization' in headers:
                # 替换为标准Bearer格式
                headers['Authorization'] = f'Bearer {api_key}'
            # 构建headers字符串
            args.headers = ';'.join([f'{k}={v}' for k, v in headers.items()])
            print(f'处理后的请求头: {headers}')
        except json.JSONDecodeError:
            print(f'错误: 模型{args.model}的customHeader不是有效的JSON')
            return

    args.max_tokens = 100  # 默认值
    args.min_tokens = 50   # 默认值
    args.api = 'openai'    # 默认值
    args.dataset = 'random'  # 默认值
    args.prefix_length = 0  # 默认值

    # 解析额外参数
    try:
        # 处理Windows命令行中可能的引号问题
        extra_args = args.extra_args.strip()
        
        # 直接尝试解析为JSON
        try:
            args.extra_args = json.loads(extra_args)
        except json.JSONDecodeError:
            # 如果失败，尝试处理常见的Windows命令行格式问题
            # 1. 移除可能的外部引号
            if (extra_args.startswith('"') and extra_args.endswith('"')) or \
               (extra_args.startswith("'") and extra_args.endswith("'")):
                extra_args = extra_args[1:-1]
                # 再次尝试解析
                try:
                    args.extra_args = json.loads(extra_args)
                except json.JSONDecodeError:
                    pass
                else:
                    # 成功解析，跳出异常处理
                    raise StopIteration
            
            # 2. 处理没有引号的键值对格式 {key: value}
            if extra_args.strip().startswith('{') and extra_args.strip().endswith('}'):
                # 使用正则表达式提取键值对
                import re
                pairs = re.findall(r'([a-zA-Z0-9_]+):\s*(.+?)(?:,|})', extra_args.strip())
                args.extra_args = {}
                for key, value in pairs:
                    value = value.strip()
                    # 转换值的类型
                    if value.lower() == 'true':
                        args.extra_args[key] = True
                    elif value.lower() == 'false':
                        args.extra_args[key] = False
                    elif value.isdigit():
                        args.extra_args[key] = int(value)
                    elif re.match(r'^\d+\.\d+$', value):
                        args.extra_args[key] = float(value)
                    elif (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        args.extra_args[key] = value[1:-1]
                    else:
                        args.extra_args[key] = value
            else:
                raise json.JSONDecodeError("Invalid JSON format", extra_args, 0)

        # 合并模型配置中的otherParams
        if model_config.get('otherParams'):
            try:
                model_other_params = json.loads(model_config['otherParams'])
                args.extra_args.update(model_other_params)
                print(f'合并模型配置后的额外参数: {args.extra_args}')
            except json.JSONDecodeError:
                print(f'警告: 模型{args.model}的otherParams不是有效的JSON，将被忽略')

    except StopIteration:
        # 成功解析，继续执行
        pass
    except json.JSONDecodeError as e:
        print(f"额外参数格式无效，无法解析为JSON。错误: {e}")
        print(f"提供的参数: {args.extra_args}")
        print(f"处理后的参数: {extra_args}")
        return

    # 加载tokenizer
    tokenizer = load_tokenizer(args.tokenizer_path)
    if not tokenizer:
        # 尝试使用当前目录
        if args.tokenizer_path != '.':
            print(f'尝试使用当前目录加载tokenizer...')
            tokenizer = load_tokenizer('.')
        if not tokenizer:
            return
    if not tokenizer:
        return

    if args.command == 'perf':
        print(f"开始性能测试: 模型={args.model}, 并发数={args.parallel}, 总次数={args.number}")

        # 使用线程池进行并发测试
        results = []
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
            future_to_test = {executor.submit(run_single_test, args, tokenizer): i for i in range(args.number)}
            for future in concurrent.futures.as_completed(future_to_test):
                test_id = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"测试 {test_id+1}/{args.number} 完成: {result}")
                except Exception as e:
                    print(f"测试 {test_id+1}/{args.number} 失败: {e}")
                    results.append({'success': False, 'error': str(e)})

        end_time = time.time()

        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        failure_count = args.number - success_count

        if success_count > 0:
            avg_input_tokens = sum(r['input_tokens'] for r in results if r['success']) / success_count
            avg_output_tokens = sum(r['output_tokens'] for r in results if r['success']) / success_count
            avg_total_tokens = sum(r['total_tokens'] for r in results if r['success']) / success_count
            avg_time = sum(r['time_taken'] for r in results if r['success']) / success_count
            avg_speed = sum(r['speed'] for r in results if r['success']) / success_count
            total_time = end_time - start_time
            throughput = success_count / total_time

            print("\n性能测试结果汇总:")
            print(f"总测试次数: {args.number}")
            print(f"成功次数: {success_count}")
            print(f"失败次数: {failure_count}")
            print(f"平均输入tokens: {avg_input_tokens:.2f}")
            print(f"平均输出tokens: {avg_output_tokens:.2f}")
            print(f"平均总tokens: {avg_total_tokens:.2f}")
            print(f"平均响应时间: {avg_time:.2f}秒")
            print(f"平均生成速度: {avg_speed:.2f} tokens/秒")
            print(f"总耗时: {total_time:.2f}秒")
            print(f"吞吐量: {throughput:.2f} 请求/秒")
        else:
            print("所有测试均失败")

    else:
        parser.print_help()

if __name__ == '__main__':
    main()