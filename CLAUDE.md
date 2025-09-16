# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains the generation system for the PixMo-Docs, CoSyn-400K, and CoSyn-point datasets. It's a Python-based pipeline system that uses LLMs to generate synthetic multimodal data including charts, tables, documents, diagrams, and other visualizations.

## Environment Setup

Install dependencies and set up environment:
```bash
conda create --name pixmo-doc python=3.10
conda activate pixmo-doc
pip install -r requirements.txt
```

Set required API keys:
```bash
export OPENAI_API_KEY=your-api-key
export ANTHROPIC_API_KEY=your-api-key
export HF_TOKEN=your-api-key  # optional, for HuggingFace uploads
```

Additional system dependencies:
- **LaTeX**: Required for LaTeX-based pipelines
- **Mermaid CLI**: `npm install -g @mermaid-js/mermaid-cli`
- **Playwright**: `pip install playwright && playwright install`
- **Additional packages**: `pip install mpl_finance<=0.10.1 mplfinance<=0.12.10b0 cairosvg<=2.7.1`

## Main Commands

### Generate synthetic data:
```bash
python main.py -p {PIPELINE} -t {TYPE} -n {NUM_SAMPLES} -m {DATASET_NAME}
```

### Example commands:
```bash
# Generate 5 bar charts using Matplotlib
python main.py -p "MatplotlibChartPipeline" -n 5 -m "matplotlib_test" -t "bar chart"

# Generate multiple pipeline types
python main.py -p "MatplotlibChartPipeline,PlotlyChartPipeline" -n 10 -t "bar chart,line chart"
```

### Key arguments:
- `-p, --pipelines`: Pipeline names (comma-separated)
- `-t, --types`: Visualization types to generate (comma-separated)
- `-n, --num`: Number of samples per pipeline
- `-l, --llm`: LLM model (default: gpt-4o)
- `-c, --code_llm`: Code generation LLM (default: claude-sonnet)
- `-s, --seed`: Random seed (default: 42)
- `-b, --batch_size`: LLM batch size (default: 24)
- `-m, --name`: Dataset name for HuggingFace upload
- `-f, --force`: Force regeneration

## Architecture

### Core Structure
- `main.py`: Entry point with argument parsing
- `pipeline/all_pipelines.py`: Main orchestrator with DataDreamer session management
- `pipeline/`: Individual pipeline implementations organized by category

### Pipeline Categories
- **Charts**: MatplotlibChartPipeline, PlotlyChartPipeline, VegaLiteChartPipeline, LaTeXChartPipeline, HTMLChartPipeline
- **Tables**: LaTeXTablePipeline, MatplotlibTablePipeline, PlotlyTablePipeline, HTMLTablePipeline
- **Documents**: LaTeXDocumentPipeline, HTMLDocumentPipeline, DOCXDocumentPipeline
- **Diagrams**: GraphvizDiagramPipeline, MermaidDiagramPipeline, LaTeXDiagramPipeline
- **Circuits**: SchemdrawCircuitPipeline, LaTeXCircuitPipeline
- **Graphics**: SVGGraphicPipeline, AsymptoteGraphicPipeline, DALLEImagePipeline, RdkitChemicalPipeline, LaTeXMathPipeline, LilyPondMusicPipeline
- **Web**: HTMLScreenPipeline, HTMLDocumentPointPipeline

### Pipeline Structure
Each pipeline follows a consistent structure:
1. **GenerateTopics**: Create topics for the visualization type
2. **GenerateData**: Generate synthetic data based on topics
3. **GenerateVisualization**: Create the actual visualization code and image
4. **GenerateQA**: Generate question-answer pairs (optional)

### Key Components
- `pipeline/utils/`: Shared utilities including LLM support, rendering helpers, and instruction generators
- DataDreamer framework integration for step orchestration and caching
- Support for both OpenAI (GPT-4o) and Anthropic (Claude Sonnet) models
- Built-in HuggingFace Hub publishing capabilities

### LLM Configuration
- Default text LLM: GPT-4o
- Default code LLM: Claude Sonnet
- Configurable batch sizes for parallel processing
- Custom Anthropic wrapper for Claude integration

### Output Structure
Generated datasets contain:
- `metadata`: Pipeline and configuration information
- `topic`: Generated topic/description
- `data`: Synthetic data used for visualization
- `code`: Generated code (Python/LaTeX/HTML/etc.)
- `image`: Rendered visualization
- `qa`: Question-answer pairs (when enabled)

Results are saved to `./session_output/` and can be published to HuggingFace Hub.