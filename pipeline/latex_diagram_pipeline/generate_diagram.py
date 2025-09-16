import os
import tempfile
import platform
import subprocess
import json
import warnings
import pandas as pd
from io import StringIO
import signal

from PIL import Image
from datasets.fingerprint import Hasher
from datadreamer.steps import DataSource, SuperStep, Prompt, zipped

from ..prompts.diagram_prompts import GENERATE_DIAGRAM_CODE_LATEX_PROMPT
from ..utils.utils import extract_latex, process_image
from ..utils.render import render_latex

NUM_RENDER_WORKERS = 4


def check_pdflatex():
    # Create a simple LaTeX document without PyLaTeX to avoid package dependencies
    latex_content = r"""\documentclass{article}
\begin{document}
\title{Test Document}
\maketitle
This is a test document to check if pdflatex is available.
\end{document}"""

    temp_dir = tempfile.mkdtemp()
    tex_file = os.path.join(temp_dir, "test_document.tex")

    try:
        # Write LaTeX content
        with open(tex_file, 'w') as f:
            f.write(latex_content)

        # Try to compile
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"pdflatex compilation failed: {result.stderr}")

    except FileNotFoundError:
        raise RuntimeError(
            "Your system must have pdflatex installed to run this pipeline. "
            "Please install TeX Live or MiKTeX."
        )
    except Exception as e:
        raise RuntimeError(
            f"Error checking pdflatex: {e}"
        )
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def check_tools():
    system = platform.system()
    required_tools = ["pdftoppm", "pdftocairo"]
    missing_tools = [
        tool
        for tool in required_tools
        if subprocess.run(["which", tool], capture_output=True).returncode != 0
    ]

    if missing_tools:
        print(f"⚠️  Warning: The following tools are not installed on {system}: {', '.join(missing_tools)}")
        print("These tools are optional but improve PDF to image conversion quality.")
        if system == "Darwin":  # macOS
            print("To install, run: brew install poppler cairo")
        elif system == "Linux":
            print("To install, run: sudo apt-get install poppler-utils cairo")
        print("Continuing without these tools...")


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException()


class GenerateDiagram(SuperStep):
    CONFIG_HASH = Hasher.hash([GENERATE_DIAGRAM_CODE_LATEX_PROMPT])

    def setup(self):
        self.register_input(
            "metadata", required=True, help="The metadata used to generate the topics."
        )
        self.register_input("topic", required=True, help="The topics.")
        self.register_input("data", required=True, help="The data.")
        self.register_arg("llm", required=True, help="The LLM to use.")
        self.register_arg(
            "batch_size", required=True, help="The batch size to use with the LLM."
        )
        self.register_output("metadata")
        self.register_output("topic")
        self.register_output("data")
        self.register_output("code")
        self.register_output("image")

    def run(self):
        combined_inputs = DataSource(
            "Combine inputs",
            {
                "metadata": list(self.inputs["metadata"]),
                "topic": list(self.inputs["topic"]),
                "data": list(self.inputs["data"]),
            },
        )

        # Create prompts
        prompts_dataset = combined_inputs.map(
            lambda row: {
                "prompt": GENERATE_DIAGRAM_CODE_LATEX_PROMPT.format(
                    topic=row["topic"],
                    figure_type=json.loads(row["metadata"])["figure_type"],
                    data=row["data"],
                    persona=json.loads(row["metadata"])["persona"],
                )
            },
            lazy=False,
            name="Create Generate Code Prompts",
        )

        # Generate Code
        generated_code = Prompt(
            name="Generate",
            inputs={
                "prompts": prompts_dataset.output["prompt"],
            },
            args={
                "llm": self.args["llm"],
                "batch_size": self.args["batch_size"],
                "post_process": extract_latex,
                "temperature": 1.0,
                "top_p": 1.0,
            },
            outputs={
                "generations": "code",
            },
        ).select_columns(["code"], name="Get Generated Code")

        # Combine with generations with inputs
        combined = zipped(
            combined_inputs, generated_code, name="Combine with inputs"
        ).save(name="Save combine with inputs")

        # Check if pdflatex and pdf2image is available
        check_pdflatex()
        check_tools()

        # Generate Images
        def execute_code_and_generate_image(row, timeout=20):
            original_dir = os.getcwd()
            os.chdir(tempfile.mkdtemp())
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)  # set the timeout
            
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    image = render_latex(row["code"])

                    if not isinstance(image, Image.Image):
                        raise TypeError()
                    
                    row["image"] = process_image(image)
            except TimeoutException:
                print(f"Error: Code execution exceeded {timeout} seconds.")
                row["image"] = None
            except Exception as e:
                print(f"Error: {e}")
                row["image"] = None
            finally:
                signal.alarm(0)  # disable the alarm
                os.chdir(original_dir)
            
            return row

        code_and_images = combined.map(
            execute_code_and_generate_image,
            lazy=False,
            name="Generate Images",
        )

        # Remove any invalid images
        filtered = code_and_images.filter(
            lambda row: row["image"] is not None,
            lazy=False,
            name="Remove invalid images",
        )
        if filtered.output.num_rows < code_and_images.output.num_rows:
            self.logger.info(
                f"Warning: Could only generate valid images for {filtered.output.num_rows} out of {code_and_images.output.num_rows} total rows."
            )

        # Return result
        return filtered.output

    @property
    def version(self):
        return hash(GenerateDiagram.CONFIG_HASH)
