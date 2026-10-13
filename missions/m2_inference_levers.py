"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing, sustainability

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}


def _budget_scenario(reasoning_requests: list[dict], total_requests: int,
                     max_share: float) -> dict:
    """Route the largest excess reasoning requests to normal small-model handling."""
    allowed = int(total_requests * max_share)
    excess = max(0, len(reasoning_requests) - allowed)
    rerouted = sorted(reasoning_requests, key=lambda item: item["tokens"], reverse=True)[:excess]
    return {
        "cap_pct": max_share * 100,
        "rerouted": excess,
        "cost_saved_daily": sum(max(0.0, item["cost"] - item["small_cost"]) for item in rerouted),
        "wh_saved_daily": sum(item["reasoning_wh"] - item["normal_wh"] for item in rerouted),
    }


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = cascade_cost = cache_cost = opt_cost = 0.0
    total_tokens = 0
    reasoning_groups = {
        False: {"requests": 0, "tokens": 0, "cost_daily": 0.0, "wh_daily": 0.0},
        True: {"requests": 0, "tokens": 0, "cost_daily": 0.0, "wh_daily": 0.0},
    }
    reasoning_requests = []
    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        is_reasoning = bool(int(num(r["is_reasoning"])))
        total_tokens += inp + out
        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)
        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        cascade_cost += pricing.request_cost(inp, out, pin, pout)
        cache_cost += pricing.request_cost(inp, out, pin, pout, cached_in=cached)
        request_usd = pricing.request_cost(inp, out, pin, pout, cached_in=cached, batch=is_batch)
        opt_cost += request_usd
        tokens = inp + out
        normal_wh = sustainability.wh_per_query(tokens)
        request_wh = sustainability.wh_per_query(tokens, is_reasoning=is_reasoning)
        group = reasoning_groups[is_reasoning]
        group["requests"] += 1
        group["tokens"] += tokens
        group["cost_daily"] += request_usd
        group["wh_daily"] += request_wh
        if is_reasoning:
            small_in, small_out = MODEL_PRICES["small"]
            reasoning_requests.append({
                "tokens": tokens, "cost": request_usd,
                "small_cost": pricing.request_cost(inp, out, small_in, small_out,
                                                   cached_in=cached, batch=is_batch),
                "reasoning_wh": request_wh, "normal_wh": normal_wh,
            })

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0
    lever_savings_daily = {
        "cascade": base_cost - cascade_cost,
        "cache": cascade_cost - cache_cost,
        "batch": cache_cost - opt_cost,
    }
    reasoning_budget = {
        "normal": reasoning_groups[False],
        "reasoning": reasoning_groups[True],
        "cap_10": _budget_scenario(reasoning_requests, len(rows), 0.10),
        "cap_5": _budget_scenario(reasoning_requests, len(rows), 0.05),
    }

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")
        rg = reasoning_budget["reasoning"]
        print(f"reasoning: {rg['requests']}/{len(rows)} requests, ${rg['cost_daily']:.2f}/day, {rg['wh_daily']:.1f} Wh/day")
        for label in ("cap_10", "cap_5"):
            scenario = reasoning_budget[label]
            print(f"cap {scenario['cap_pct']:.0f}%: reroute {scenario['rerouted']}, "
                  f"save ${scenario['cost_saved_daily']:.2f}/day and {scenario['wh_saved_daily']:.1f} Wh/day")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "lever_savings_daily": lever_savings_daily,
        "reasoning_budget": reasoning_budget,
    }


if __name__ == "__main__":
    run()
