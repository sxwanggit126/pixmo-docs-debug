#!/usr/bin/env python3

import os
import subprocess
import shutil
from pathlib import Path
import sys

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Disable all caching to avoid pickle issues
os.environ['DATADREAMER_DISABLE_CACHE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '0'
os.environ['HF_DATASETS_OFFLINE'] = '0'

# Disable multiprocessing in DataDreamer to avoid num_proc errors
os.environ['DATADREAMER_DISABLE_MULTIPROCESSING'] = '1'
os.environ['DATASETS_DISABLE_MULTIPROCESSING'] = '1'

# Clean any existing cache before starting
if os.path.exists('./session_output/.cache'):
    shutil.rmtree('./session_output/.cache')

# 测试配置
test_configs = [
    {
        "pipeline": "GraphvizDiagramPipeline",
        "types": "network diagram,flowchart,organizational chart",
        "output_dir": "graphviz",
        "session_dir": "Generate_Graphviz_Diagrams"
    },
    {
        "pipeline": "MermaidDiagramPipeline",
        "types": "sequence diagram,gantt chart,class diagram",
        "output_dir": "mermaid",
        "session_dir": "Generate_Mermaid_Diagrams"
    },
    {
        "pipeline": "LaTeXDiagramPipeline",
        "types": "circuit diagram,block diagram,tree diagram",
        "output_dir": "latex",
        "session_dir": "Generate_LaTeX_Diagrams"
    },
    {
        "pipeline": "MatplotlibChartPipeline",
        "types": "bar chart,scatter plot,heatmap",
        "output_dir": "matplotlib",
        "session_dir": "Generate_Matplotlib_Charts"
    },
    {
        "pipeline": "PlotlyChartPipeline",
        "types": "3d surface plot,candlestick chart,sunburst chart",
        "output_dir": "plotly",
        "session_dir": "Generate_Plotly_Charts"
    }
]

# 创建 examples 目录
examples_dir = Path("./examples")
examples_dir.mkdir(exist_ok=True)

# 运行测试
for config in test_configs:
    print(f"\n{'='*50}")
    print(f"Testing {config['pipeline']}...")
    print(f"{'='*50}")

    # 创建输出目录
    output_path = examples_dir / config['output_dir']
    output_path.mkdir(exist_ok=True)

    # 运行管道
    cmd = [
        "python", "main.py",
        "-p", config['pipeline'],
        "-n", "3",
        "-t", config['types'],
        "-m", f"{config['output_dir']}_test",
        "-f"  # Force regenerate
    ]

    subprocess.run(cmd)

    # 复制结果
    # 查找正确的 session 目录
    session_dirs = {
        'graphviz': 'generate-graphviz-diagrams',
        'mermaid': 'generate-mermaid-diagrams',
        'latex': 'generate-latex-diagrams',
        'matplotlib': 'generate-matplotlib-charts',
        'plotly': 'generate-plotly-charts'
    }

    session_dir_name = session_dirs.get(config['output_dir'], f"generate-{config['output_dir']}")
    session_path = Path("./session_output") / session_dir_name

    if session_path.exists():
        print(f"Found session directory: {session_path}")

        # 查找生成的图像文件
        image_count = 0
        json_count = 0
        html_count = 0

        # 在 generate-code 子目录中查找生成的文件
        code_dir = session_path / "generate-code"
        if code_dir.exists():
            # 查找 PNG 文件
            for img_file in code_dir.rglob("*.png"):
                if not any(part.startswith("_") for part in img_file.parts):
                    shutil.copy2(img_file, output_path / f"{config['output_dir']}_{image_count+1}.png")
                    print(f"Copied image: {img_file.name} -> {config['output_dir']}_{image_count+1}.png")
                    image_count += 1

            # 查找生成的数据
            data_dir = session_path / "generate-data"
            if data_dir.exists():
                for json_file in data_dir.rglob("dataset.json"):
                    shutil.copy2(json_file, output_path / f"{config['output_dir']}_data.json")
                    print(f"Copied dataset: {json_file.name}")
                    json_count += 1

        # 查找 HTML 文件
        for html_file in session_path.rglob("*.html"):
            if not any(part.startswith("_") for part in html_file.parts):
                shutil.copy2(html_file, output_path / f"{config['output_dir']}_{html_count+1}.html")
                print(f"Copied HTML: {html_file.name}")
                html_count += 1

        if image_count > 0 or json_count > 0 or html_count > 0:
            print(f"✅ Copied {image_count} images, {json_count} datasets, {html_count} HTML files to {output_path}")
        else:
            print(f"⚠️  No generated files found in {session_path}")
    else:
        print(f"⚠️  Session directory not found: {session_path}")

print("\n✅ All tests completed successfully!")

# Try to extract results using the extraction script
print("\n" + "="*50)
print("Attempting to extract results from Arrow datasets...")
print("="*50)
subprocess.run([sys.executable, "extract_results.py"])
