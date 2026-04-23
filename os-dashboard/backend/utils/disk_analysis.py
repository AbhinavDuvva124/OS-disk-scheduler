"""Enhanced disk analysis with smart recommendations."""
from typing import List, Dict, Any


def analyze_disk_algorithms(results: Dict[str, Any]) -> Dict[str, Any]:
    if not results:
        return {}

    algos = list(results.keys())
    seeks = {a: results[a].get("total_seek", float("inf")) for a in algos}
    times = {a: results[a].get("total_time_ms", float("inf")) for a in algos}
    variances = {a: results[a].get("seek_variance", float("inf")) for a in algos}
    fairness  = {a: results[a].get("fairness_index", 0) for a in algos}

    best_seek     = min(seeks, key=seeks.get)
    best_time     = min(times, key=times.get)
    best_variance = min(variances, key=variances.get)
    best_fairness = max(fairness, key=fairness.get)

    # Score: weighted multi-metric
    scores = {a: 0 for a in algos}
    for a in algos:
        scores[a] += (1 - seeks[a] / max(seeks.values())) * 40       # 40% weight on seek
        scores[a] += (1 - variances[a] / max(variances.values())) * 25 if max(variances.values()) > 0 else 25
        scores[a] += fairness[a] * 20
        scores[a] += (1 - times[a] / max(times.values())) * 15 if max(times.values()) > 0 else 15

    overall_best = max(scores, key=scores.get)

    # Smart recommendation logic
    req_spread = _get_request_spread(results)
    recommendation = _smart_recommend(overall_best, req_spread, seeks, variances, fairness)

    # Starvation aggregation
    starvation_warnings = []
    for a, data in results.items():
        for w in data.get("starvation_warnings", []):
            starvation_warnings.append({**w, "algorithm": a})

    insights = _generate_insights(results, seeks, variances, fairness, best_seek)

    return {
        "overall_best":   overall_best,
        "scores":         {a: round(scores[a], 2) for a in algos},
        "best_per_metric": {
            "total_seek":     {"algo": best_seek,     "value": seeks[best_seek]},
            "total_time_ms":  {"algo": best_time,     "value": times[best_time]},
            "seek_variance":  {"algo": best_variance, "value": variances[best_variance]},
            "fairness_index": {"algo": best_fairness, "value": fairness[best_fairness]},
        },
        "insights":              insights,
        "recommendation":        recommendation,
        "starvation_warnings":   starvation_warnings,
    }


def _get_request_spread(results):
    try:
        seq = list(results.values())[0].get("seek_sequence", [])
        if len(seq) < 2: return 0
        return max(seq) - min(seq)
    except Exception:
        return 0


def _smart_recommend(best: str, spread: int, seeks, variances, fairness) -> str:
    algo_display = {
        "FCFS": "FCFS", "SSTF": "SSTF", "SCAN": "SCAN",
        "CSCAN": "C-SCAN", "LOOK": "LOOK", "CLOOK": "C-LOOK",
        "NSTEP": "N-Step SCAN", "FSCAN": "FSCAN",
    }
    name = algo_display.get(best, best)

    recs = {
        "FCFS":  f"FCFS is ideal only for very light or ordered workloads. For this spread ({spread} cylinders), consider LOOK or SSTF instead.",
        "SSTF":  f"SSTF minimizes total seek for this workload but risks starvation of outer tracks. Use with a starvation timeout.",
        "SCAN":  f"SCAN (Elevator) provides balanced performance. Great for medium-density workloads like this one ({spread} cyl spread).",
        "CSCAN": f"C-SCAN ensures uniform wait times — recommended when fairness matters more than raw throughput.",
        "LOOK":  f"LOOK outperforms SCAN by avoiding unnecessary travel to disk boundaries. Best choice for this pattern.",
        "CLOOK": f"C-LOOK combines LOOK's efficiency with C-SCAN's uniformity — excellent for streaming workloads.",
        "NSTEP": f"N-Step SCAN prevents indefinite postponement and handles bursty arrivals — suitable for mixed I/O systems.",
        "FSCAN": f"FSCAN's two-queue design prevents new requests from delaying current queue — ideal for high-arrival-rate systems.",
    }
    return recs.get(best, f"Recommended: {name} for this workload pattern.")


def _generate_insights(results, seeks, variances, fairness, best_seek) -> List[str]:
    insights = []
    algos = list(results.keys())

    # Seek comparison
    worst_seek = max(seeks, key=seeks.get)
    if seeks[worst_seek] > 0:
        improvement = round((1 - seeks[best_seek] / seeks[worst_seek]) * 100, 1)
        if improvement > 10:
            insights.append(f"{best_seek} reduces total seek distance by {improvement}% vs {worst_seek}.")

    # Variance
    best_var = min(algos, key=lambda a: variances[a])
    if variances[best_var] < min(v for k, v in variances.items() if k != best_var) * 0.7:
        insights.append(f"{best_var} has the most consistent seek pattern (variance = {variances[best_var]:.2f}).")

    # Fairness
    best_fair = max(algos, key=lambda a: fairness[a])
    insights.append(f"{best_fair} achieves the best fairness index ({fairness[best_fair]:.3f}), minimizing request discrimination.")

    # Starvation warnings
    any_starvation = any(results[a].get("starvation_warnings") for a in algos)
    if any_starvation:
        insights.append("⚠ Starvation detected in some algorithms — consider SCAN or LOOK variants for fairness.")

    # LOOK vs SCAN
    if "SCAN" in seeks and "LOOK" in seeks and seeks["LOOK"] < seeks["SCAN"]:
        diff = seeks["SCAN"] - seeks["LOOK"]
        insights.append(f"LOOK saves {diff} cylinders over SCAN by not seeking to disk boundaries.")

    return insights


def smart_workload_recommendation(requests: List[int], head: int, disk_size: int) -> Dict[str, Any]:
    """Analyze request pattern and recommend best algorithm."""
    if not requests:
        return {"recommendation": "No requests to analyze."}

    spread = max(requests) - min(requests) if requests else 0
    density = len(requests) / disk_size if disk_size else 0
    avg_dist_from_head = sum(abs(r - head) for r in requests) / len(requests) if requests else 0

    pattern = "random"
    sorted_req = sorted(requests)
    diffs = [sorted_req[i+1] - sorted_req[i] for i in range(len(sorted_req)-1)]
    if diffs and max(diffs) < disk_size * 0.1:
        pattern = "clustered"
    elif all(d > 0 for d in diffs):
        pattern = "sequential"
    elif spread > disk_size * 0.8:
        pattern = "scatter"

    rec_map = {
        "clustered":  ("SSTF",  "Requests are clustered — SSTF will minimize seek with low starvation risk."),
        "sequential": ("LOOK",  "Sequential pattern — LOOK sweeps efficiently without boundary overhead."),
        "scatter":    ("CSCAN", "Wide scatter — C-SCAN ensures uniform service times across all tracks."),
        "random":     ("LOOK",  "Random pattern — LOOK provides the best balance of seek reduction and fairness."),
    }
    algo, reason = rec_map.get(pattern, ("LOOK", "LOOK is a robust general-purpose choice."))

    return {
        "pattern":              pattern,
        "spread":               spread,
        "density":              round(density, 4),
        "avg_dist_from_head":   round(avg_dist_from_head, 2),
        "recommended_algorithm": algo,
        "reason":               reason,
    }
