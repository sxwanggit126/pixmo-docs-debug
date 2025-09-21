# pixmo-docs

This is the repository for the generation system of the [PixMo-Docs](https://huggingface.co/datasets/allenai/pixmo-docs), [CoSyn-400K](https://huggingface.co/datasets/allenai/CoSyn-400K), and [CoSyn-point](https://huggingface.co/datasets/allenai/CoSyn-point) datasets. PixMo-Docs was used to train the [Molmo](https://arxiv.org/abs/2409.17146) model, and the CoSyn datasets are an expanded version that use an improved pipeline and more types of documents. More details can be found in our [paper](https://arxiv.org/pdf/2502.14846).

## 🆕 New Features

This enhanced version includes the following improvements over the original repository:

- **Modern Package Management**: Uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python dependency management with `pyproject.toml`
- **Flexible API Configuration**: Supports both official APIs and proxy services (like OpenRouter) via `.env` configuration
- **Batch Testing Script**: Includes `test_pipelines.py` for automated testing of multiple pipelines
- **Environment Variables**: All API keys and configurations managed through `.env` file for better security
- **Improved Error Handling**: Enhanced multiprocessing patches and better error recovery
- **Dual Language Documentation**: Both English and Chinese README files

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Using uv (Recommended)

After cloning the repo, you can set up the project using uv:

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Install additional dependencies for specific pipelines
uv pip install playwright && playwright install
uv pip install mpl_finance<=0.10.1 mplfinance<=0.12.10b0 cairosvg<=2.7.1
```

### Traditional Installation (Alternative)

```bash
conda create --name pixmo-doc python=3.10
conda activate pixmo-doc
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the project root with your API keys:

```bash
# API Mode: "official" or "proxy"
API_MODE=official

# Official API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
HF_TOKEN=your-huggingface-token  # Optional, for uploading datasets

# Proxy Configuration (if API_MODE=proxy)
PROXY_API_KEY=your-proxy-key
PROXY_BASE_URL=https://api.openrouter.ai/v1
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### System Dependencies

Some pipelines require additional system dependencies:

1. **LaTeX**: Install based on your OS from [official LaTeX website](https://www.latex-project.org/get/)
   ```bash
   # macOS
   brew install --cask mactex
   # Ubuntu/Debian
   sudo apt-get install texlive-full
   ```

2. **Mermaid CLI**:
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

3. **PDF Tools** (for LaTeX pipelines):
   ```bash
   # macOS
   brew install poppler
   # Ubuntu/Debian
   sudo apt-get install poppler-utils
   ```

## Quick Start

### Basic Usage

Generate synthetic data using the main script:

```bash
python main.py -p {PIPELINE} \
               -t {TYPE_OF_DATA} \
               -n {NUMBER_OF_SAMPLES} \
               -m {DATASET_NAME}
```

Example:
```bash
python main.py -p "MatplotlibChartPipeline" -n 5 -m "matplotlib_test" -t "bar chart"
```

### Batch Testing

Test multiple pipelines at once:

```bash
python test_pipelines.py
```

This will test all configured pipelines and save results to the `examples/` directory.

### Advanced Usage

Generate multiple types with different pipelines:
```bash
python main.py -p "MatplotlibChartPipeline,PlotlyChartPipeline" \
               -n 10 \
               -t "bar chart,line chart,scatter plot" \
               -m "combined_charts"
```

### Command Line Arguments

- `-p, --pipelines`: Pipeline names (comma-separated)
- `-t, --types`: Visualization types to generate (comma-separated)
- `-n, --num`: Number of samples per pipeline
- `-l, --llm`: LLM model for text generation (default: gpt-4o)
- `-c, --code_llm`: LLM for code generation (default: claude-3-5-sonnet)
- `-s, --seed`: Random seed (default: 42)
- `-b, --batch_size`: LLM batch size (default: 24)
- `-m, --name`: Dataset name for HuggingFace upload
- `-f, --force`: Force regeneration, ignore cache

## Pipelines

We support 25 pipelines across 8 categories:

### Charts
- **MatplotlibChartPipeline**: Traditional charts using Matplotlib
- **PlotlyChartPipeline**: Interactive charts with Plotly
- **VegaLiteChartPipeline**: Declarative charts with Vega-Lite
- **LaTeXChartPipeline**: Charts using TikZ
- **HTMLChartPipeline**: Simple charts with HTML/CSS

### Tables
- **LaTeXTablePipeline**: Complex structured tables
- **MatplotlibTablePipeline**: Tables within figures
- **PlotlyTablePipeline**: Simple interactive tables
- **HTMLTablePipeline**: Web-based tables

### Documents
- **LaTeXDocumentPipeline**: Scientific documents and reports
- **HTMLDocumentPipeline**: Web documents with rich styling
- **DOCXDocumentPipeline**: Microsoft Word documents

### Diagrams
- **GraphvizDiagramPipeline**: Graph and tree structures
- **MermaidDiagramPipeline**: Flowcharts and sequence diagrams
- **LaTeXDiagramPipeline**: Technical diagrams with TikZ

### Circuits
- **SchemDrawCircuitPipeline**: Electrical circuit diagrams
- **LaTeXCircuitPipeline**: Circuits using CircuiTikZ

### Specialized Graphics
- **DALLEImagePipeline**: AI-generated images
- **RdkitChemicalPipeline**: Chemical structure diagrams
- **LaTeXMathPipeline**: Mathematical expressions
- **LilyPondMusicPipeline**: Sheet music notation
- **SVGGraphicPipeline**: Vector graphics
- **AsymptoteGraphicPipeline**: Mathematical/technical graphics

### Web Screens
- **HTMLScreenPipeline**: Web page screenshots

### Pointing
- **HTMLDocumentPointPipeline**: Documents with pointing annotations

## Troubleshooting

### Common Issues

1. **DataDreamer multiprocessing errors**: Already patched in this version
2. **LaTeX missing packages**: Install `texlive-full` or equivalent
3. **Plotly export issues**: Ensure `kaleido` is installed: `uv pip install kaleido`
4. **API rate limits**: Adjust `batch_size` parameter or use proxy services

### Debug Mode

Enable detailed logging:
```bash
export DATADREAMER_DISABLE_CACHE=1
python main.py -p "PlotlyChartPipeline" -n 1 -t "bar chart" -f
```

## Citation

Please cite the following papers if you use this codebase or our datasets:

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