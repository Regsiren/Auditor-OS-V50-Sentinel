#!/usr/bin/env python3
"""
True 3-strata Hugging Face residual-stream hook demo (Dual-Head ARIA).

Registers PyTorch forward hooks on three explicit transformer layers
(early / mid / late — prefer indices 4, 16, 30 when depth allows; otherwise
proportionally remapped), builds a true ``[3, seq_len, d_model]`` tensor for
``PrefillSentinelAuditor``, then runs Stage II ``HardenedHomeostaticSentinelCore``
decode steps with real unembedding weights when available.

Run from repository root:
  pip install -r requirements-ai.txt
  python examples/demo_huggingface_hook.py
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from auditor_ai import HardenedHomeostaticSentinelCore, PrefillSentinelAuditor


PREFERRED_MODELS = ("gpt2", "Qwen/Qwen2.5-0.5B")
REFERENCE_STRATA = (4, 16, 30)  # early, mid, late on a ≥31-layer stack
NUM_NEW_TOKENS = 10
PROMPT = "The Sentinel Protocol observes residual"


def resolve_strata_indices(n_layers: int) -> Tuple[int, int, int]:
    """Map reference strata (4, 16, 30) onto the actual transformer depth."""
    if n_layers <= 0:
        raise ValueError("n_layers must be > 0")
    if n_layers > max(REFERENCE_STRATA):
        return REFERENCE_STRATA
    scale = (n_layers - 1) / float(max(REFERENCE_STRATA))
    return tuple(min(n_layers - 1, max(0, round(t * scale))) for t in REFERENCE_STRATA)  # type: ignore[return-value]


def _count_blocks(model: nn.Module) -> int:
    if hasattr(model, "transformer") and hasattr(model.transformer, "h"):
        return len(model.transformer.h)
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return len(model.model.layers)
    raise AttributeError("Could not count residual blocks")


def _resolve_block_module(model: nn.Module, layer_index: int) -> nn.Module:
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
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}"


def _load_model_with_fallback() -> Tuple[nn.Module, Any, str, bool]:
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

    class _FallbackLM(nn.Module):
        def __init__(self, n_layer: int = 32, hidden: int = 64, vocab: int = 128) -> None:
            super().__init__()
            self.config = type("C", (), {"n_embd": hidden, "hidden_size": hidden})()
            self.embed = nn.Embedding(vocab, hidden)
            self.transformer = nn.Module()
            self.transformer.h = nn.ModuleList(
                [nn.Sequential(nn.Linear(hidden, hidden), nn.Tanh()) for _ in range(n_layer)]
            )
            self.lm_head = nn.Linear(hidden, vocab, bias=False)

        def get_output_embeddings(self) -> nn.Linear:
            return self.lm_head

        def forward(self, input_ids: torch.Tensor) -> Any:
            x = self.embed(input_ids)
            for block in self.transformer.h:
                x = block(x) + x
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
            ids = [(ord(c) % 127) + 1 for c in text[:32]] or [1]
            return torch.tensor([ids], dtype=torch.long)

    return _FallbackLM(), _FallbackTokenizer(), "fallback-residual-tower-32L", False


def _get_unembedding(model: nn.Module) -> Optional[torch.Tensor]:
    """Return ``(V, d_model)`` output embedding / unembedding weights when present."""
    try:
        if hasattr(model, "get_output_embeddings"):
            emb = model.get_output_embeddings()
            if emb is not None and hasattr(emb, "weight"):
                return emb.weight.detach().float()
        if hasattr(model, "lm_head") and hasattr(model.lm_head, "weight"):
            return model.lm_head.weight.detach().float()
    except Exception:
        return None
    return None


def run_hooked_generation(num_new_tokens: int = NUM_NEW_TOKENS) -> List[dict]:
    model, tokenizer, label, is_real = _load_model_with_fallback()
    n_layers = _count_blocks(model)
    early_i, mid_i, late_i = resolve_strata_indices(n_layers)
    strata = {"early": early_i, "mid": mid_i, "late": late_i}

    # Capture last-token residual per stratum on each forward.
    captured: Dict[str, torch.Tensor] = {}

    def _make_hook(name: str):
        def _hook(_module: nn.Module, _inp: Any, out: Any) -> None:
            hidden = out[0] if isinstance(out, (tuple, list)) else out
            if not torch.is_tensor(hidden):
                return
            captured[name] = hidden[:, -1, :].detach()  # (batch, d)

        return _hook

    handles = []
    for name, idx in strata.items():
        handles.append(_resolve_block_module(model, idx).register_forward_hook(_make_hook(name)))

    unembedding = _get_unembedding(model)
    d_model = int(unembedding.shape[1]) if unembedding is not None else 64
    if unembedding is None:
        # Infer d_model from a dry-run fallback embed.
        d_model = int(getattr(getattr(model, "config", None), "n_embd", None)
                      or getattr(getattr(model, "config", None), "hidden_size", 64))

    telemetry: List[dict] = []

    print("=" * 78)
    print("  THOHAT V50-S  |  True 3-Strata Dual-Head HF Hook Demo")
    print("=" * 78)
    print(f"Model / tower : {label}")
    print(f"Strata hooks  : early={early_i}, mid={mid_i}, late={late_i} (n_layers={n_layers})")
    print(f"Unembedding   : {'yes (get_output_embeddings)' if unembedding is not None else 'synthetic fallback'}")
    print(f"Mode          : {'Hugging Face' if is_real else 'offline fallback'}")
    print("-" * 78)

    try:
        input_ids = tokenizer.encode(PROMPT, return_tensors="pt")
        if not torch.is_tensor(input_ids):
            input_ids = torch.tensor(input_ids, dtype=torch.long)
        if input_ids.ndim == 1:
            input_ids = input_ids.unsqueeze(0)

        # --- Stage I Prefill: one forward to populate 3 strata over prompt tokens ---
        # Collect per-token strata by re-running with growing prefix for demo clarity,
        # then stack as [3, seq, d]. For efficiency we sample last-token per prefix step.
        prompt_len = int(input_ids.shape[1])
        early_seq, mid_seq, late_seq = [], [], []
        with torch.no_grad():
            for t in range(1, prompt_len + 1):
                captured.clear()
                _ = model(input_ids[:, :t])
                if not all(k in captured for k in strata):
                    raise RuntimeError("3-strata hooks did not all fire during prefill.")
                early_seq.append(captured["early"][0])
                mid_seq.append(captured["mid"][0])
                late_seq.append(captured["late"][0])

        prompt_3strata = torch.stack(
            [
                torch.stack(early_seq, dim=0),
                torch.stack(mid_seq, dim=0),
                torch.stack(late_seq, dim=0),
            ],
            dim=0,
        )  # [3, seq, d]
        d_model = int(prompt_3strata.shape[-1])

        prefill_auditor = PrefillSentinelAuditor(d_model=d_model)
        stage1 = prefill_auditor.forward(prompt_3strata)
        print(
            f"[Stage I] Ω_prefill={stage1.omega_prefill:.4f}  "
            f"discordance={stage1.contraction_discordance:.4f}  "
            f"veto={stage1.prefill_veto}  centroids={tuple(stage1.centroids.shape)}"
        )
        if stage1.prefill_veto:
            print("[+] 0-token prefill save — decode aborted; `.sent` bag minted.")
            print(f"    bag keys: {list((stage1.sent_bag or {}).keys())}")
            return [{"stage": "prefill", "Omega_t": stage1.omega_prefill, "topological_veto": True}]

        core_kwargs: Dict[str, Any] = {"d_model": d_model}
        if unembedding is not None and unembedding.shape[1] == d_model:
            core_kwargs["embedding_table"] = unembedding
            core_kwargs["vocab_size"] = int(unembedding.shape[0])
        core = HardenedHomeostaticSentinelCore(**core_kwargs)
        core.seed_from_prefill(stage1)

        print(f"{'step':>4}  {'Ω_t':>10}  {'macro':>8}  {'a_orth':>10}  {'steer':>5}  phase")
        with torch.no_grad():
            for step in range(1, num_new_tokens + 1):
                captured.clear()
                outputs = model(input_ids)
                logits = outputs.logits if hasattr(outputs, "logits") else outputs[0]
                next_id = torch.argmax(logits[:, -1, :], dim=-1, keepdim=True)
                input_ids = torch.cat([input_ids, next_id], dim=-1)

                if not all(k in captured for k in strata):
                    raise RuntimeError("3-strata hooks did not fire during decode.")
                # Unified residual = mean across strata last-token vectors.
                theta = torch.stack(
                    [captured["early"][0], captured["mid"][0], captured["late"][0]], dim=0
                ).mean(dim=0)
                step_logits = logits[0, -1, :].detach()
                result = core.forward(
                    theta,
                    logits=step_logits if step_logits.numel() == core.vocab_size else None,
                    informational_content=float(torch.linalg.vector_norm(theta).item()),
                )
                row = {
                    "step": step,
                    "Omega_t": result.omega_t,
                    "macro_dist": result.macro_dist,
                    "a_orthogonal": result.a_orthogonal,
                    "phase_state": result.phase_state.value,
                    "topological_veto": result.topological_veto,
                    "slow_burn_veto": result.slow_burn_veto,
                    "actuation_applied": result.actuation_applied,
                }
                telemetry.append(row)
                print(
                    f"{step:4d}  {result.omega_t:10.6f}  {result.macro_dist:8.4f}  "
                    f"{result.a_orthogonal:10.4e}  {str(result.actuation_applied):>5}  "
                    f"{result.phase_state.name}"
                )
                if result.topological_veto:
                    print("[+] Stage II topological veto — `.sent` bag minted.")
                    break
    finally:
        for h in handles:
            h.remove()

    print("-" * 78)
    print("=" * 78)
    return telemetry


if __name__ == "__main__":
    run_hooked_generation()
