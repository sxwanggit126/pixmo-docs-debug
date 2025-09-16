"""
DataDreamer patch to fix num_proc errors
"""

import os
import warnings

# Force disable all multiprocessing
os.environ['DATADREAMER_DISABLE_MULTIPROCESSING'] = '1'
os.environ['DATASETS_DISABLE_MULTIPROCESSING'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Patch datasets library to avoid num_proc issues
try:
    import datasets.arrow_dataset

    # Save original map function
    _original_map = datasets.arrow_dataset.Dataset.map

    def patched_map(self, function, *args, **kwargs):
        # Remove any num_proc related arguments
        if 'num_proc' in kwargs:
            kwargs['num_proc'] = 1
        if 'save_num_proc' in kwargs:
            del kwargs['save_num_proc']

        return _original_map(self, function, *args, **kwargs)

    # Apply patch
    datasets.arrow_dataset.Dataset.map = patched_map

except ImportError:
    pass

# Patch datadreamer to avoid multiprocessing issues
try:
    import datadreamer.steps.step

    # Override default num_proc behavior
    original_init = datadreamer.steps.step.Step.__init__

    def patched_init(self, *args, **kwargs):
        result = original_init(self, *args, **kwargs)
        # Force disable multiprocessing for all steps
        if hasattr(self, '_dataset_map_kwargs'):
            self._dataset_map_kwargs['num_proc'] = 1
        return result

    datadreamer.steps.step.Step.__init__ = patched_init

except ImportError:
    pass

print("✅ DataDreamer multiprocessing patches applied")