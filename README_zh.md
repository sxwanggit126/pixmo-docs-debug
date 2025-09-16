# pixmo-docs

这是 [PixMo-Docs](https://huggingface.co/datasets/allenai/pixmo-docs)、[CoSyn-400K](https://huggingface.co/datasets/allenai/CoSyn-400K) 和 [CoSyn-point](https://huggingface.co/datasets/allenai/CoSyn-point) 数据集生成系统的代码仓库。PixMo-Docs 被用于训练 [Molmo](https://arxiv.org/abs/2409.17146) 模型，而 CoSyn 数据集是使用改进的流程和更多类型文档的扩展版本。更多细节可以在我们的[论文](https://arxiv.org/pdf/2502.14846)中找到。

## 🆕 新增功能

此增强版本相比原始仓库包含以下改进：

- **现代化包管理**：使用 [uv](https://github.com/astral-sh/uv) 进行快速、可靠的 Python 依赖管理，配合 `pyproject.toml`
- **灵活的 API 配置**：通过 `.env` 配置支持官方 API 和代理服务（如 OpenRouter）
- **批量测试脚本**：包含 `test_pipelines.py` 用于自动化测试多个管道
- **环境变量管理**：所有 API 密钥和配置通过 `.env` 文件管理，提升安全性
- **改进的错误处理**：增强的多进程补丁和更好的错误恢复机制
- **双语文档**：提供英文和中文 README 文件

## 安装

### 前置要求

- Python 3.10 或更高版本
- [uv](https://github.com/astral-sh/uv) 包管理器

### 使用 uv（推荐）

克隆仓库后，使用 uv 设置项目：

```bash
# 如果尚未安装，先安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Windows 上使用: .venv\Scripts\activate
uv pip install -r requirements.txt

# 为特定管道安装额外依赖
uv pip install playwright && playwright install
uv pip install mpl_finance<=0.10.1 mplfinance<=0.12.10b0 cairosvg<=2.7.1
```

### 传统安装方式（备选）

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

某些管道需要额外的系统依赖：

1. **LaTeX**：根据您的操作系统从[官方 LaTeX 网站](https://www.latex-project.org/get/)安装
   ```bash
   # macOS
   brew install --cask mactex
   # Ubuntu/Debian
   sudo apt-get install texlive-full
   ```

2. **Mermaid CLI**：
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

3. **PDF 工具**（用于 LaTeX 管道）：
   ```bash
   # macOS
   brew install poppler
   # Ubuntu/Debian
   sudo apt-get install poppler-utils
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

### 批量测试

一次测试多个管道：

```bash
python test_pipelines.py
```

这将测试所有配置的管道并将结果保存到 `examples/` 目录。

### 高级用法

使用不同管道生成多种类型：
```bash
python main.py -p "MatplotlibChartPipeline,PlotlyChartPipeline" \
               -n 10 \
               -t "bar chart,line chart,scatter plot" \
               -m "combined_charts"
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

## 管道

我们支持 8 个类别的 25 个管道：

### 图表
- **MatplotlibChartPipeline**：使用 Matplotlib 的传统图表
- **PlotlyChartPipeline**：使用 Plotly 的交互式图表
- **VegaLiteChartPipeline**：使用 Vega-Lite 的声明式图表
- **LaTeXChartPipeline**：使用 TikZ 的图表
- **HTMLChartPipeline**：使用 HTML/CSS 的简单图表

### 表格
- **LaTeXTablePipeline**：复杂结构表格
- **MatplotlibTablePipeline**：图形中的表格
- **PlotlyTablePipeline**：简单交互式表格
- **HTMLTablePipeline**：基于网页的表格

### 文档
- **LaTeXDocumentPipeline**：科学文档和报告
- **HTMLDocumentPipeline**：富样式的网页文档
- **DOCXDocumentPipeline**：Microsoft Word 文档

### 图表
- **GraphvizDiagramPipeline**：图和树结构
- **MermaidDiagramPipeline**：流程图和序列图
- **LaTeXDiagramPipeline**：使用 TikZ 的技术图表

### 电路
- **SchemDrawCircuitPipeline**：电路图
- **LaTeXCircuitPipeline**：使用 CircuiTikZ 的电路

### 专业图形
- **DALLEImagePipeline**：AI 生成的图像
- **RdkitChemicalPipeline**：化学结构图
- **LaTeXMathPipeline**：数学表达式
- **LilyPondMusicPipeline**：乐谱
- **SVGGraphicPipeline**：矢量图形
- **AsymptoteGraphicPipeline**：数学/技术图形

### 网页屏幕
- **HTMLScreenPipeline**：网页截图

### 指向
- **HTMLDocumentPointPipeline**：带指向标注的文档

## 故障排除

### 常见问题

1. **DataDreamer 多进程错误**：此版本已修补
2. **LaTeX 缺少包**：安装 `texlive-full` 或等效包
3. **Plotly 导出问题**：确保安装了 `kaleido`：`uv pip install kaleido`
4. **API 速率限制**：调整 `batch_size` 参数或使用代理服务

### 调试模式

启用详细日志：
```bash
export DATADREAMER_DISABLE_CACHE=1
python main.py -p "PlotlyChartPipeline" -n 1 -t "bar chart" -f
```

## 引用

如果您在工作中使用此代码库或我们的数据集，请引用以下论文：

```bibtex
@article{yang2025scaling,
      title={Scaling Text-Rich Image Understanding via Code-Guided Synthetic Multimodal Data Generation},
      author={Yang, Yue and Patel, Ajay and Deitke, Matt and Gupta, Tanmay and Weihs, Luca and Head, Andrew and Yatskar, Mark and Callison-Burch, Chris and Krishna, Ranjay and Kembhavi, Aniruddha and others},
      journal={arXiv preprint arXiv:2502.14846},
      year={2025}
}
```

```bibtex
@article{deitke2024molmo,
  title={Molmo and pixmo: Open weights and open data for state-of-the-art multimodal models},
  author={Deitke, Matt and Clark, Christopher and Lee, Sangho and Tripathi, Rohun and Yang, Yue and Park, Jae Sung and Salehi, Mohammadreza and Muennighoff, Niklas and Lo, Kyle and Soldaini, Luca and others},
  journal={arXiv preprint arXiv:2409.17146},
  year={2024}
}
```