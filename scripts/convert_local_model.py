"""Convertit un modèle HF (GPT-NeoX, entraîné sur Colab) au format LitGPT.

    python scripts/convert_local_model.py models/local/modele-fr-rn

Le dossier doit contenir model.safetensors et config.json (le .zip de Colab).
Si model_config.yaml manque, il est créé à partir de config.json.
Produit lit_model.pth dans le même dossier.
"""

import json
import sys
from pathlib import Path

import torch
import yaml
from safetensors.torch import load_file

from litgpt.config import Config
from litgpt.model import GPT
from litgpt.scripts.convert_hf_checkpoint import copy_weights_gpt_neox


def config_depuis_hf(folder: Path) -> dict:
    hf = json.loads((folder / "config.json").read_text())
    rotary = hf.get("partial_rotary_factor") or hf.get("rotary_pct") or (hf.get("rope_parameters") or {}).get(
        "partial_rotary_factor", 0.25
    )
    return {
        "name": folder.name,
        "hf_config": {},
        "block_size": hf["max_position_embeddings"],
        "vocab_size": hf["vocab_size"],
        "padded_vocab_size": hf["vocab_size"],
        "n_layer": hf["num_hidden_layers"],
        "n_head": hf["num_attention_heads"],
        "n_embd": hf["hidden_size"],
        "n_query_groups": hf["num_attention_heads"],
        "head_size": hf["hidden_size"] // hf["num_attention_heads"],
        "rotary_percentage": rotary,
        "rope_base": hf.get("rope_theta") or hf.get("rotary_emb_base", 10000),
        "parallel_residual": hf.get("use_parallel_residual", True),
        "bias": True,
        "lm_head_bias": False,
        "norm_class_name": "LayerNorm",
        "norm_eps": hf.get("layer_norm_eps", 1e-5),
        "mlp_class_name": "GptNeoxMLP",
        "intermediate_size": hf["intermediate_size"],
        "gelu_approximate": "none",
    }


folder = Path(sys.argv[1])
fichier_config = folder / "model_config.yaml"
if not fichier_config.exists():
    fichier_config.write_text(yaml.safe_dump(config_depuis_hf(folder), sort_keys=False))
    print("Créé :", fichier_config)
config = Config(**yaml.safe_load(fichier_config.read_text()))
state_dict = {}
copy_weights_gpt_neox(config, state_dict, load_file(folder / "model.safetensors"))
# Vérifie que toutes les clés correspondent au modèle LitGPT
GPT(config).load_state_dict(state_dict, strict=True)
torch.save(state_dict, folder / "lit_model.pth")
print("OK:", folder / "lit_model.pth", len(state_dict), "tenseurs")
