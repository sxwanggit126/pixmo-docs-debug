[english](README_en.md)
# pixmo-docs

这是 [PixMo-Docs](https://huggingface.co/datasets/allenai/pixmo-docs)、[CoSyn-400K](https://huggingface.co/datasets/allenai/CoSyn-400K) 和 [CoSyn-point](https://huggingface.co/datasets/allenai/CoSyn-point) 数据集生成系统的代码仓库。PixMo-Docs 被用于训练 [Molmo](https://arxiv.org/abs/2409.17146) 模型，而 CoSyn 数据集是使用改进的流程和更多类型文档的扩展版本。更多细节可以在我们的[论文](https://arxiv.org/pdf/2502.14846)中找到。

## 新增功能
- **arrow文件转成jsonl格式**: 把代码生成的合成数据转变成jsonl格式
```shell
# 自动发现session_output目录下数据集
# ===================
# 1. 转换特定数据集
# ===================
python convert.py --dataset generate-mermaid-diagrams

# ===================
# 2. session_output 目录下的所有数据集
# ===================
python convert.py --session-dir session_output
```

### 传统安装方式

```bash
conda create --name pixmo-doc python=3.10
conda activate pixmo-doc
pip install -r requirements.txt
```

### 环境配置

在项目根目录创建 `.env` 文件，配置您的 API 密钥：

```bash
# API 模式: "official" 或 "proxy"
API_MODE=official

# 官方 API 密钥
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
HF_TOKEN=your-huggingface-token  # 可选，用于上传数据集

# 代理配置（如果 API_MODE=proxy）
PROXY_API_KEY=your-proxy-key
PROXY_BASE_URL=https://api.openrouter.ai/v1
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### 系统依赖

mermaid管道需要额外的系统依赖：

- **Mermaid CLI**：
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

## 快速开始

### 基础用法

使用主脚本生成合成数据：

```bash
python main.py -p {管道名称} \
               -t {数据类型} \
               -n {样本数量} \
               -m {数据集名称}
```

示例：
```bash
python main.py -p "MatplotlibChartPipeline" -n 5 -m "matplotlib_test" -t "bar chart"
```


Mermaid管道生成训练数据：
```shell
python main.py -p "MermaidDiagramPipeline" \
-n 10 -t "flowchart,sequence diagram,class diagram" \
-m "mermaid_types"
```


### 命令行参数

- `-p, --pipelines`：管道名称（逗号分隔）
- `-t, --types`：要生成的可视化类型（逗号分隔）
- `-n, --num`：每个管道的样本数量
- `-l, --llm`：用于文本生成的 LLM 模型（默认：gpt-4o）
- `-c, --code_llm`：用于代码生成的 LLM（默认：claude-3-5-sonnet）
- `-s, --seed`：随机种子（默认：42）
- `-b, --batch_size`：LLM 批处理大小（默认：24）
- `-m, --name`：用于 HuggingFace 上传的数据集名称
- `-f, --force`：强制重新生成，忽略缓存

