# Copyright Lightning AI. Licensed under the Apache License 2.0, see LICENSE file.
"""Data modules kept for the document platform.

- DataModule / SFTDataset: base classes to build new document datasets.
- JSON: instruction fine-tuning on your own JSON files (main entry point).
- TextFiles: continued pretraining on a folder of plain .txt documents.
- Alpaca: small public dataset, kept as the default to quickly test fine-tuning.
"""

from litgpt.data.alpaca import Alpaca
from litgpt.data.base import DataModule, SFTDataset, get_sft_collate_fn
from litgpt.data.json_data import JSON
from litgpt.data.text_files import TextFiles

__all__ = ["Alpaca", "DataModule", "JSON", "SFTDataset", "TextFiles", "get_sft_collate_fn"]
