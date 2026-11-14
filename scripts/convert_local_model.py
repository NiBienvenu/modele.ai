"""Convertit un modèle HF (GPT-NeoX, entraîné sur Colab) au format LitGPT.

    python scripts/convert_local_model.py models/local/modele-fr-rn

Le dossier doit contenir model.safetensors et model_config.yaml.
Produit lit_model.pth dans le même dossier.
"""

import sys
from pathlib import Path

import torch
import yaml
from safetensors.torch import load_file

from litgpt.config import Config
from litgpt.model import GPT
from litgpt.scripts.convert_hf_checkpoint import copy_weights_gpt_neox

folder = Path(sys.argv[1])
config = Config(**yaml.safe_load((folder / "model_config.yaml").read_text()))
state_dict = {}
copy_weights_gpt_neox(config, state_dict, load_file(folder / "model.safetensors"))
# Vérifie que toutes les clés correspondent au modèle LitGPT
GPT(config).load_state_dict(state_dict, strict=True)
torch.save(state_dict, folder / "lit_model.pth")
print("OK:", folder / "lit_model.pth", len(state_dict), "tenseurs")
