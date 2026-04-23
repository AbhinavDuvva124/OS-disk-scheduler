"""Utility calculations and analysis"""
from typing import List, Dict, Any


def analyze_cpu_algorithms(results: Dict[str, Any]) -> Dict[str, Any]:
    """Intelligent analysis of scheduling algorithm results"""
    if not results:
        return {}

    metrics_by_algo = {}
    for algo, data in results.items():
        if "metrics" in data:
            metrics_by_algo[algo] = data["metrics"]

    if not metrics_by_algo:
        return {}

    # Find best algorithm per metric
    best_avg_wait = min(metrics_by_algo.items(), key=lambda x: x[1].get("avg_waiting_time", float("inf")))
    best_turnaround = min(metrics_by_algo.items(), key=lambda x: x[1].get("avg_turnaround_time", float("inf")))
    best_response = min(metrics_by_algo.items(), key=lambda x: x[1].get("avg_response_time", float("inf")))
    best_cpu_util = max(metrics_by_algo.items(), key=lambda x: x[1].get("cpu_utilization", 0))
    best_throughput = max(metrics_by_algo.items(), key=lambda x: x[1].get("throughput", 0))

    # Score each algorithm (lower rank = better)
    scores = {algo: 0 for algo in metrics_by_algo}
    scores[best_avg_wait[0]] += 3
    scores[best_turnaround[0]] += 3
    scores[best_response[0]] += 2
    scores[best_cpu_util[0]] += 1
    scores[best_throughput[0]] += 2

    overall_best = max(scores.items(), key=lambda x: x[1])[0]

    analysis = {
        "overall_best": overall_best,
        "scores": scores,
        "best_per_metric": {
            "avg_waiting_time": {"algo": best_avg_wait[0], "value": best_avg_wait[1].get("avg_waiting_time")},
            "avg_turnaround_time": {"algo": best_turnaround[0], "value": best_turnaround[1].get("avg_turnaround_time")},
            "avg_response_time": {"algo": best_response[0], "value": best_response[1].get("avg_response_time")},
            "cpu_utilization": {"algo": best_cpu_util[0], "value": best_cpu_util[1].get("cpu_utilization")},
            "throughput": {"algo": best_throughput[0], "value": best_throughput[1].get("throughput")},
        },
        "insights": _generate_cpu_insights(metrics_by_algo, overall_best, best_avg_wait, best_response),
        "recommendation": _generate_recommendation(overall_best, metrics_by_algo),
    }
    return analysis


def _generate_cpu_insights(metrics_by_algo, overall_best, best_wait, best_response):
    insights = []

    algo_names = {
        "FCFS": "First-Come First-Served",
        "SJF": "Shortest Job First",
        "RR": "Round Robin",
        "Priority": "Priority Scheduling",
    }

    if overall_best == "FCFS":
        insights.append("FCFS works well when processes have similar burst times — no convoy effect observed.")
    if overall_best == "SJF":
        insights.append("SJF minimizes average waiting time by serving shortest jobs first — optimal for batch systems.")
    if overall_best == "RR":
        insights.append("Round Robin provides fair CPU distribution — excellent for time-sharing and interactive systems.")
    if overall_best == "Priority":
        insights.append("Priority Scheduling excels when high-priority tasks must complete quickly — ideal for real-time systems.")

    # Compare response times
    if "RR" in metrics_by_algo:
        rr_resp = metrics_by_algo["RR"].get("avg_response_time", 0)
        fcfs_resp = metrics_by_algo.get("FCFS", {}).get("avg_response_time", float("inf"))
        if rr_resp < fcfs_resp:
            insights.append(f"Round Robin achieves {round(fcfs_resp - rr_resp, 2)} units better average response time than FCFS.")

    if "SJF" in metrics_by_algo:
        sjf_wait = metrics_by_algo["SJF"].get("avg_waiting_time", 0)
        insights.append(f"SJF achieves the theoretical minimum average waiting time of {sjf_wait} units for this workload.")

    return insights


def _generate_recommendation(best: str, metrics):
    recs = {
        "FCFS": (
            "Recommended for batch processing systems where simplicity is preferred "
            "and all jobs have similar execution times."
        ),
        "SJF": (
            "Recommended for maximizing throughput in batch environments where burst times "
            "are known in advance. Watch out for starvation of long processes."
        ),
        "RR": (
            "Recommended for interactive and time-sharing systems. Adjust the time quantum "
            "to balance response time vs. context-switching overhead."
        ),
        "Priority": (
            "Recommended for real-time or mixed-priority systems. Consider aging mechanisms "
            "to prevent starvation of low-priority processes."
        ),
    }
    return recs.get(best, "No specific recommendation available.")


def analyze_disk_algorithms(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze disk scheduling results"""
    if not results:
        return {}

    seeks = {algo: data.get("total_seek", float("inf")) for algo, data in results.items()}
    best_algo = min(seeks.items(), key=lambda x: x[1])

    insights = []
    if "SSTF" in seeks and "FCFS" in seeks:
        diff = seeks["FCFS"] - seeks["SSTF"]
        if diff > 0:
            insights.append(f"SSTF reduces total seek time by {diff} cylinders compared to FCFS.")

    if "SCAN" in seeks:
        insights.append("SCAN prevents starvation by servicing all requests in a sweep direction.")

    if "CSCAN" in seeks:
        insights.append("C-SCAN provides more uniform wait times by always sweeping in one direction.")

    if best_algo[0] == "SSTF":
        insights.append("SSTF performs best here but may cause starvation for far-away requests.")

    return {
        "best_algorithm": best_algo[0],
        "total_seeks": seeks,
        "insights": insights,
        "recommendation": _disk_recommendation(best_algo[0]),
    }


def _disk_recommendation(best: str) -> str:
    recs = {
        "FCFS": "Use FCFS for systems with light disk load where fairness is critical.",
        "SSTF": "Use SSTF for heavy disk loads where throughput matters more than fairness.",
        "SCAN": "Use SCAN for a balance between performance and fairness — prevents starvation.",
        "CSCAN": "Use C-SCAN for the most uniform response times across all disk positions.",
    }
    return recs.get(best, "")
