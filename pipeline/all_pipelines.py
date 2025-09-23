import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Apply DataDreamer patches before importing anything else
from pipeline.utils.datadreamer_patches import *

from pipeline.utils.anthropic_support import CustomAnthropic

from datadreamer import DataDreamer
from datadreamer.llms import OpenAI
from datadreamer.steps import concat

from .matplotlib_chart_pipeline import MatplotlibChartPipeline
from .vegalite_chart_pipeline import VegaLiteChartPipeline
from .plotly_chart_pipeline import PlotlyChartPipeline
from .latex_chart_pipeline import LaTeXChartPipeline
from .html_chart_pipeline import HTMLChartPipeline

from .latex_table_pipeline import LaTeXTablePipeline
from .matplotlib_table_pipeline import MatplotlibTablePipeline
from .plotly_table_pipeline import PlotlyTablePipeline
from .html_table_pipeline import HTMLTablePipeline

from .latex_document_pipeline import LaTeXDocumentPipeline
from .html_document_pipeline import HTMLDocumentPipeline
from .docx_document_pipeline import DOCXDocumentPipeline

from .graphviz_diagram_pipeline import GraphvizDiagramPipeline
from .latex_diagram_pipeline import LaTeXDiagramPipeline
from .mermaid_diagram_pipeline import MermaidDiagramPipeline

from .dalle_image_pipeline import DALLEImagePipeline

from .rdkit_chemical_pipeline import RdkitChemicalPipeline
from .latex_math_pipeline import LaTeXMathPipeline
from .lilypond_music_pipeline import LilyPondMusicPipeline
from .schemdraw_circuit_pipeline import SchemdrawCircuitPipeline
from .latex_circuit_pipeline import LaTeXCircuitPipeline

from .svg_graphic_pipeline import SVGGraphicPipeline
from .asymptote_graphic_pipeline import AsymptoteGraphicPipeline

from .html_document_point_pipeline import HTMLDocumentPointPipeline
from .html_screen_pipeline import HTMLScreenPipeline


def create_llm_instance(model_name, api_key=None, system_prompt="You are a helpful data scientist.", api_mode=None):
    """
    根据 API 模式创建相应的 LLM 实例
    """
    if api_mode is None:
        api_mode = os.getenv("API_MODE", "official")

    if api_mode == "official":
        # Official API mode - use direct API access
        if "gpt" in model_name.lower():
            return OpenAI(
                model_name=model_name,
                api_key=api_key,
                system_prompt=system_prompt,
                base_url=os.getenv("OPENAI_BASE_URL")
            )
        elif "claude" in model_name.lower():
            return CustomAnthropic(
                model_name=model_name,
                api_key=api_key,
                base_url=os.getenv("ANTHROPIC_BASE_URL")
            )

    elif api_mode == "proxy":
        # Proxy mode - use unified proxy API for all models
        from pipeline.utils.proxy_llm_fixed import ProxyLLM
        return ProxyLLM(
            model_name=model_name,
            system_prompt=system_prompt
        )

    elif api_mode == "azure":
        # Azure mode - use Azure OpenAI for all models
        from pipeline.utils.azure_llm import AzureLLM
        return AzureLLM(
            model_name=model_name,
            system_prompt=system_prompt
        )

    else:
        raise ValueError(f"Unsupported API mode: {api_mode}")


def run_datadreamer_session(args):
    if args.qa:
        os.environ["GENERATE_QA"] = "true"
    else:
        os.environ["GENERATE_QA"] = "false"

    with DataDreamer("./session_output"):
        # Get API mode and model configurations from environment
        api_mode = os.getenv("API_MODE", "official")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        openai_mini_model = os.getenv("OPENAI_MINI_MODEL", "gpt-4o-mini")
        anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")

        print(f"API Mode: {api_mode}")
        print(f"Models - OpenAI: {openai_model}, OpenAI Mini: {openai_mini_model}, Anthropic: {anthropic_model}")

        # Create LLM instances based on API mode
        try:
            gpt_4o = create_llm_instance(
                model_name=openai_model,
                api_key=args.openai_api_key,
                system_prompt="You are a helpful data scientist.",
                api_mode=api_mode
            )
            print(f"✅ Created main LLM: {openai_model}")
        except Exception as e:
            print(f"❌ Failed to create main LLM ({openai_model}): {e}")
            raise

        try:
            gpt_4o_mini = create_llm_instance(
                model_name=openai_mini_model,
                api_key=args.openai_api_key,
                system_prompt="You are a helpful data scientist.",
                api_mode=api_mode
            )
            print(f"✅ Created mini LLM: {openai_mini_model}")
        except Exception as e:
            print(f"❌ Failed to create mini LLM ({openai_mini_model}): {e}")
            raise

        try:
            # For Azure mode, Claude models will be mapped to GPT deployments
            if api_mode == "azure":
                claude_sonnet = create_llm_instance(
                    model_name=anthropic_model,
                    api_key=None,  # Azure uses AD authentication
                    system_prompt="You are a helpful data scientist.",
                    api_mode=api_mode
                )
            else:
                claude_sonnet = create_llm_instance(
                    model_name=anthropic_model,
                    api_key=args.anthropic_api_key,
                    system_prompt="You are a helpful data scientist.",
                    api_mode=api_mode
                )
            print(f"✅ Created code LLM: {anthropic_model}")
        except Exception as e:
            print(f"❌ Failed to create code LLM ({anthropic_model}): {e}")
            raise

        # Map LLM arguments to actual instances
        llm_mapping = {
            "gpt-4o": gpt_4o,
            "gpt-4o-mini": gpt_4o_mini,
            "claude-3-7-sonnet-20250219": claude_sonnet,
            "claude-sonnet": claude_sonnet  # Alias
        }

        # Select main LLM
        if args.llm in llm_mapping:
            llm = llm_mapping[args.llm]
        else:
            print(f"⚠️  Unknown LLM '{args.llm}', defaulting to gpt-4o")
            llm = gpt_4o

        # Select code LLM
        if args.code_llm in llm_mapping:
            code_llm = llm_mapping[args.code_llm]
        else:
            print(f"⚠️  Unknown code LLM '{args.code_llm}', defaulting to claude-sonnet")
            code_llm = claude_sonnet

        print(f"Selected LLM: {args.llm} -> {type(llm).__name__}")
        print(f"Selected Code LLM: {args.code_llm} -> {type(code_llm).__name__}")

        # Choose which pipelines to run
        pipelines = {
            "Generate Matplotlib Charts": MatplotlibChartPipeline,
            "Generate Vega-Lite Charts": VegaLiteChartPipeline,
            "Generate Plotly Charts": PlotlyChartPipeline,
            "Generate LaTeX Charts": LaTeXChartPipeline,
            "Generate HTML Charts": HTMLChartPipeline,
            "Generate LaTeX Tables": LaTeXTablePipeline,
            "Generate Matplotlib Tables": MatplotlibTablePipeline,
            "Generate Plotly Tables": PlotlyTablePipeline,
            "Generate HTML Tables": HTMLTablePipeline,
            "Generate LaTeX Documents": LaTeXDocumentPipeline,
            "Generate HTML Documents": HTMLDocumentPipeline,
            "Generate DOCX Documents": DOCXDocumentPipeline,
            "Generate Graphviz Diagrams": GraphvizDiagramPipeline,
            "Generate LaTeX Diagrams": LaTeXDiagramPipeline,
            "Generate Mermaid Diagrams": MermaidDiagramPipeline,
            "Generate DALL-E Images": DALLEImagePipeline,
            "Generate Chemical Structures": RdkitChemicalPipeline,
            "Generate LaTeX Math": LaTeXMathPipeline,
            "Generate Lilypond Music": LilyPondMusicPipeline,
            "Generate SchemDraw Circuits": SchemdrawCircuitPipeline,
            "Generate LaTeX Circuits": LaTeXCircuitPipeline,
            "Generate SVG Graphics": SVGGraphicPipeline,
            "Generate Asymptote Graphics": AsymptoteGraphicPipeline,
            "Generate HTML Points": HTMLDocumentPointPipeline,
            "Generate HTML Screens": HTMLScreenPipeline,
        }
        pipelines = {
            k: v
            for k, v in pipelines.items()
            if v.__name__ in [p.strip() for p in args.pipelines.split(",")]
        }

        # Choose how many visualizes per pipeline
        if "," in args.num:
            nums = [int(n.strip()) for n in args.num.strip(",")]
            assert len(nums) == len(
                pipelines), f"Number of counts ({len(nums)}) must match number of pipelines ({len(pipelines)})"
        else:
            nums = [int(args.num)] * len(pipelines)

        # Get figure types
        figure_types = [figure_type.strip() for figure_type in args.types.split(",")]

        print(f"\n🚀 Running {len(pipelines)} pipelines:")
        for (pipeline_name, pipeline), num in zip(pipelines.items(), nums):
            print(f"  - {pipeline_name}: {num} items")

        # Run each selected pipeline
        synthetic_visuals = [
            pipeline(
                pipeline_name,
                args={
                    "llm": llm,
                    "code_llm": code_llm,
                    "batch_size": args.batch_size,
                    "code_batch_size": args.code_batch_size,
                    "n": num,
                    "seed": args.seed,
                    "figure_types": figure_types,
                    "qa": args.qa,
                },
                force=args.force,
            )
            for num, (pipeline_name, pipeline) in zip(nums, pipelines.items())
        ]

        # Combine results from each pipeline
        scifi_dataset = concat(
            *synthetic_visuals, name="Combine results from all pipelines"
        )

        # Preview n rows of the dataset
        print("\n📊 Dataset Preview:")
        print(scifi_dataset.head(n=5))

        # Push to HuggingFace Hub
        print(f"\n📤 Publishing to HuggingFace Hub: {args.name}")
        scifi_dataset.publish_to_hf_hub(args.name, private=True)
        print("✅ Successfully published to HuggingFace Hub!")