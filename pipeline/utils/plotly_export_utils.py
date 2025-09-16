"""
Utility functions for Plotly image export with fallback options
"""

import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
from io import BytesIO
import warnings


def safe_plotly_to_image(fig, width=800, height=600):
    """
    Safely convert a Plotly figure to PIL Image with multiple fallback methods.

    Args:
        fig: Plotly figure object
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        PIL Image object or None if all methods fail
    """

    # Method 1: Try standard to_image with explicit parameters
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            img_bytes = fig.to_image(
                format='png',
                width=width,
                height=height,
                scale=2.0
            )
            return Image.open(BytesIO(img_bytes))
    except Exception:
        pass

    # Method 2: Try with minimal parameters
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            img_bytes = fig.to_image()
            return Image.open(BytesIO(img_bytes))
    except Exception:
        pass

    # Method 3: Try write_image to BytesIO
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            img_io = BytesIO()
            fig.write_image(img_io, format='png')
            img_io.seek(0)
            return Image.open(img_io)
    except Exception:
        pass

    # Method 4: Use matplotlib as fallback (only for simple charts)
    try:
        return plotly_to_matplotlib_fallback(fig)
    except Exception:
        pass

    return None


def plotly_to_matplotlib_fallback(fig):
    """
    Convert simple Plotly charts to matplotlib as a fallback.
    Only supports basic chart types.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # Create matplotlib figure
    plt.figure(figsize=(8, 6))

    # Extract data from plotly figure
    for trace in fig.data:
        if hasattr(trace, 'x') and hasattr(trace, 'y'):
            if trace.type == 'scatter':
                plt.plot(trace.x, trace.y, marker='o' if trace.mode == 'markers' else '')
            elif trace.type == 'bar':
                plt.bar(trace.x, trace.y)
            # Add more chart types as needed

    # Extract layout info
    if fig.layout.title:
        plt.title(fig.layout.title.text if hasattr(fig.layout.title, 'text') else str(fig.layout.title))
    if fig.layout.xaxis and fig.layout.xaxis.title:
        plt.xlabel(fig.layout.xaxis.title.text if hasattr(fig.layout.xaxis.title, 'text') else str(fig.layout.xaxis.title))
    if fig.layout.yaxis and fig.layout.yaxis.title:
        plt.ylabel(fig.layout.yaxis.title.text if hasattr(fig.layout.yaxis.title, 'text') else str(fig.layout.yaxis.title))

    # Save to BytesIO
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    plt.close()

    img_buffer.seek(0)
    return Image.open(img_buffer)


# Template for safe plotly image generation
SAFE_PLOTLY_TEMPLATE = '''
def generate_plot(df):
    """Generate a plot using Plotly and return as PIL Image."""
    import plotly.graph_objects as go
    import plotly.express as px
    from PIL import Image
    from io import BytesIO
    import warnings

    # Your figure creation code here
    fig = ...  # Create your plotly figure

    # Safe image conversion with fallback
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Try standard conversion
            img_bytes = fig.to_image(format='png', width=800, height=600)
            img = Image.open(BytesIO(img_bytes))
    except Exception:
        # Fallback: create a placeholder image
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'Plotly Export Failed\\nShowing Placeholder',
                 ha='center', va='center', fontsize=20)
        plt.axis('off')

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        plt.close()

        img_buffer.seek(0)
        img = Image.open(img_buffer)

    return img
'''