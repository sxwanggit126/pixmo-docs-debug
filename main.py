import os
from argparse import ArgumentParser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Apply DataDreamer patches before importing anything else
from pipeline.utils.datadreamer_patches import *

from pipeline import run_datadreamer_session
from pipeline.utils.gpt4o_support import datadreamer_gpt4o_support


def validate_config():
    """Validate environment configuration based on API mode."""
    api_mode = os.getenv("API_MODE", "official")

    print(f"\n=== Configuration Validation ===")
    print(f"API Mode: {api_mode}")

    if api_mode == "official":
        # Check official API requirements
        required_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            print(f"\nERROR: Missing required environment variables for official mode:")
            print(f"  {', '.join(missing_vars)}")
            print(f"\nPlease set these variables in your .env file or environment.")
            return False

    elif api_mode == "proxy":
        # Check proxy API requirements
        required_vars = ["PROXY_API_KEY", "PROXY_BASE_URL"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            print(f"\nERROR: Missing required environment variables for proxy mode:")
            print(f"  {', '.join(missing_vars)}")
            print(f"\nPlease set these variables in your .env file or environment.")
            return False

    elif api_mode == "azure":
        # Check Azure OpenAI requirements
        required_vars = [
            "AZURE_OPENAI_TENANT_ID",
            "AZURE_OPENAI_CLIENT_ID",
            "AZURE_OPENAI_CLIENT_SECRET",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_VERSION"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            print(f"\nERROR: Missing required environment variables for Azure mode:")
            print(f"  {', '.join(missing_vars)}")
            print(f"\nPlease set these variables in your .env file or environment.")
            return False

        # Check deployment mappings
        deployment_vars = [
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_MINI_DEPLOYMENT",
            "AZURE_ANTHROPIC_DEPLOYMENT"
        ]
        missing_deployments = [var for var in deployment_vars if not os.getenv(var)]

        if missing_deployments:
            print(f"\nWARNING: Missing Azure deployment mappings:")
            print(f"  {', '.join(missing_deployments)}")
            print(f"Default deployment names will be used.")

    else:
        print(f"\nERROR: Invalid API_MODE '{api_mode}'. Valid options: official, proxy, azure")
        return False

    # Display model configuration
    print(f"\nModel Configuration:")
    print(f"  OpenAI Model: {os.getenv('OPENAI_MODEL', 'gpt-4o')}")
    print(f"  OpenAI Mini Model: {os.getenv('OPENAI_MINI_MODEL', 'gpt-4o-mini')}")
    print(f"  Anthropic Model: {os.getenv('ANTHROPIC_MODEL', 'claude-3-7-sonnet-20250219')}")

    if api_mode == "official":
        print(f"\nAPI Endpoints:")
        print(f"  OpenAI: {os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1 (default)')}")
        print(f"  Anthropic: {os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com (default)')}")
    elif api_mode == "proxy":
        print(f"\nProxy Endpoint: {os.getenv('PROXY_BASE_URL')}")
    elif api_mode == "azure":
        print(f"\nAzure Configuration:")
        print(f"  Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"  API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
        print(f"  Tenant ID: {os.getenv('AZURE_OPENAI_TENANT_ID', 'Not set')}")
        print(f"\nAzure Deployments:")
        print(f"  OpenAI Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o (default)')}")
        print(f"  OpenAI Mini Deployment: {os.getenv('AZURE_OPENAI_MINI_DEPLOYMENT', 'gpt-4o-mini (default)')}")
        print(f"  Anthropic Deployment: {os.getenv('AZURE_ANTHROPIC_DEPLOYMENT', 'gpt-4 (default)')}")

    print(f"\n=== Configuration Valid ===\n")
    return True


def main(args):
    with datadreamer_gpt4o_support():
        run_datadreamer_session(args)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-o",
        "--openai_api_key",
        type=str,
        default=os.getenv("OPENAI_API_KEY"),
        help="The OpenAI secret key.",
    )
    parser.add_argument(
        "-a",
        "--anthropic_api_key",
        type=str,
        default=os.getenv("ANTHROPIC_API_KEY"),
        help="The Anthropic secret key.",
    )
    parser.add_argument(
        "-l",
        "--llm",
        type=str,
        default="gpt-4o",
        help="LLM to use (gpt-4 or claude-sonnet).",
    )
    parser.add_argument(
        "-c",
        "--code_llm",
        type=str,
        default="claude-sonnet",
        help="LLM to use (gpt-4 or claude-sonnet) for code generation.",
    )
    parser.add_argument(
        "-p",
        "--pipelines",
        type=str,
        default="MatplotlibChartPipeline",
        help="Which pipelines to run comma-separated.",
    )
    parser.add_argument(
        "-n",
        "--num",
        type=str,
        default="1",
        help="The number of visualizations to generate per pipeline. (either a single number or a comma-separated list of numbers)",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=42,
        help="The seed to use for generation.",
    )
    parser.add_argument(
        "-b",
        "--batch_size",
        type=int,
        default=24,
        help="The number of requests to make to the LLM in parallel.",
    )
    parser.add_argument(
        "-cb",
        "--code_batch_size",
        type=int,
        default=24,
        help="The number of requests to make to the coding LLM in parallel.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force regenerate.",
    )
    parser.add_argument(
        "-m",
        "--name",
        type=str,
        default="scifi",
        help="The name of the dataset to push to huggingface.",
    )
    parser.add_argument(
        "-t",
        "--types",
        type=str,
        default="bar chart",
        help="The types of visualizations to generate.",
    )
    parser.add_argument(
        "-q",
        "--qa",
        type=bool,
        default=True,
        help="whether to generate QA for the visualizations.",
    )

    args = parser.parse_args()

    # Validate configuration before proceeding
    if not validate_config():
        exit(1)

    print("LLM:", args.llm)
    print("Code LLM:", args.code_llm)
    print("Pipelines:", args.pipelines)
    print("Num:", args.num)
    print("Seed:", args.seed)
    print("Batch Size:", args.batch_size)
    print("Code Batch Size:", args.code_batch_size)
    print("Name:", args.name)
    print("Types:", args.types)

    main(args)