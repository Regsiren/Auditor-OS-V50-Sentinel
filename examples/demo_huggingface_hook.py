#!/usr/bin/env python3
"""
Model-in-the-loop residual-stream hook demo (AI Homeostasis / Pillar I).

Loads a small open-weights Causal LM (prefers ``gpt2``, falls back gracefully if
``transformers`` or model weights are unavailable), registers
``SentinelActivationAuditor`` on transformer block index 5 (layer 6), and runs a
10-token greedy generation loop while printing per-step telemetry:

  Omega_t (Ω_t), J_tau (|θ̈|), phase_state, titration_breach

Run from repository root:
  pip install -r requirements-ai.txt
  python examples/demo_huggingface_hook.py
"""

from __future__ import annotations

import os
import sys
from typing import Any, Callable, List, Optional, Tuple

import torch
import torch.nn as nn

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from auditor_ai import SentinelActivationAuditor


PREFERRED_MODELS = ("gpt2", "Qwen/Qwen2.5-0.5B")
LAYER_INDEX = 5  # 0-based → "layer 6"
NUM_NEW_TOKENS = 10
PROMPT = "The Sentinel Protocol observes residual"


def _resolve_block_module(model: nn.Module, layer_index: int) -> nn.Module:
    """Locate the residual-stream block for GPT-2 / Qwen2-style architectures."""
    if hasattr(model, "transformer") and hasattr(model.transformer, "h"):
        blocks = model.transformer.h
        if layer_index < len(blocks):
            return blocks[layer_index]
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        blocks = model.model.layers
        if layer_index < len(blocks):
            return blocks[layer_index]
    raise AttributeError(
        "Could not resolve residual block path "
        "(expected model.transformer.h[*] or model.model.layers[*])."
    )


def _try_load_hf_model(
    model_id: str,
) -> Tuple[Optional[nn.Module], Optional[Any], Optional[str]]:
    """Attempt to load tokenizer + model. Returns (model, tokenizer, error)."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        return None, None, f"transformers not installed ({exc})"

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(model_id)
        model.eval()
        return model, tokenizer, None
    except Exception as exc:  # network / cache / auth failures
        return None, None, f"{type(exc).__name__}: {exc}"


def _load_model_with_fallback() -> Tuple[nn.Module, Any, str, bool]:
    """
    Load the first available preferred model.

    Returns
    -------
    model, tokenizer_or_none, label, is_real_hf
    """
    errors: List[str] = []
    for model_id in PREFERRED_MODELS:
        model, tokenizer, err = _try_load_hf_model(model_id)
        if model is not None and tokenizer is not None:
            print(f"[+] Loaded Hugging Face model: {model_id}")
            return model, tokenizer, model_id, True
        errors.append(f"  - {model_id}: {err}")

    print("[!] Hugging Face model unavailable; using local fallback residual tower.")
    for line in errors:
        print(line)

    # Tiny deterministic tower so the hook path remains demonstrable offline.
    class _FallbackLM(nn.Module):
        def __init__(self, n_layer: int = 8, hidden: int = 64, vocab: int = 128) -> None:
            super().__init__()
            self.embed = nn.Embedding(vocab, hidden)
            self.transformer = nn.Module()
            self.transformer.h = nn.ModuleList(
                [nn.Sequential(nn.Linear(hidden, hidden), nn.Tanh()) for _ in range(n_layer)]
            )
            self.lm_head = nn.Linear(hidden, vocab, bias=False)

        def forward(self, input_ids: torch.Tensor) -> Any:
            x = self.embed(input_ids)
            for block in self.transformer.h:
                x = block(x) + x  # residual
            logits = self.lm_head(x)

            class _Out:
                pass

            out = _Out()
            out.logits = logits
            return out

    class _FallbackTokenizer:
        eos_token_id = 0
        pad_token_id = 0

        def encode(self, text: str, return_tensors: str = "pt") -> torch.Tensor:
            # Deterministic char-hash tokens (bounded vocab).
            ids = [(ord(c) % 127) + 1 for c in text[:32]] or [1]
            t = torch.tensor([ids], dtype=torch.long)
            return t

    return _FallbackLM(), _FallbackTokenizer(), "fallback-residual-tower", False


def run_hooked_generation(
    num_new_tokens: int = NUM_NEW_TOKENS,
    layer_index: int = LAYER_INDEX,
) -> List[dict]:
    model, tokenizer, label, is_real = _load_model_with_fallback()
    auditor = SentinelActivationAuditor(rolling_window=30, omega_deviation_scale=0.12)
    telemetry: List[dict] = []
    latest_result: List[Any] = []

    def _hook(_module: nn.Module, _inp: Any, out: Any) -> None:
        hidden = out[0] if isinstance(out, (tuple, list)) else out
        if not torch.is_tensor(hidden):
            return
        # Last-token residual vector for this decode step.
        residual = hidden[:, -1, :].detach()
        result = auditor.forward(residual)
        latest_result.clear()
        latest_result.append(result)

    block = _resolve_block_module(model, layer_index)
    handle = block.register_forward_hook(_hook)

    print("=" * 72)
    print("  THOHAT V50-S  |  Hugging Face Residual-Stream Hook Demo")
    print("=" * 72)
    print(f"Model / tower : {label}")
    print(f"Hook target   : block index {layer_index} (layer {layer_index + 1})")
    print(f"Mode          : {'Hugging Face' if is_real else 'offline fallback'}")
    print("-" * 72)
    print(f"{'step':>4}  {'Omega_t':>10}  {'J_tau':>12}  {'breach':>6}  phase")

    try:
        input_ids = tokenizer.encode(PROMPT, return_tensors="pt")
        if not torch.is_tensor(input_ids):
            input_ids = torch.tensor(input_ids, dtype=torch.long)
        if input_ids.ndim == 1:
            input_ids = input_ids.unsqueeze(0)

        with torch.no_grad():
            for step in range(1, num_new_tokens + 1):
                outputs = model(input_ids)
                logits = outputs.logits if hasattr(outputs, "logits") else outputs[0]
                next_id = torch.argmax(logits[:, -1, :], dim=-1, keepdim=True)
                input_ids = torch.cat([input_ids, next_id], dim=-1)

                if not latest_result:
                    raise RuntimeError("Forward hook did not fire; check block path.")

                result = latest_result[0]
                j_tau = abs(result.acceleration)
                row = {
                    "step": step,
                    "Omega_t": result.omega_t,
                    "J_tau": j_tau,
                    "titration_breach": result.titration_breach,
                    "phase_state": result.phase_state.value,
                    "theta": result.theta,
                    "fatigue_coefficient": result.fatigue_coefficient,
                    "topological_veto": result.topological_veto,
                }
                telemetry.append(row)
                print(
                    f"{step:4d}  {result.omega_t:10.6f}  {j_tau:12.4e}  "
                    f"{str(result.titration_breach):>6}  {result.phase_state.name}"
                )
    finally:
        handle.remove()

    summary = auditor.audit_summary()
    print("-" * 72)
    print(f"Summary: {summary}")
    print("=" * 72)
    return telemetry


if __name__ == "__main__":
    run_hooked_generation()
