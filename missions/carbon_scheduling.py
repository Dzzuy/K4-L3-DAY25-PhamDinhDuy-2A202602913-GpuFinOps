"""So sánh vùng chạy cho job có thể tạm dừng và tiếp tục."""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from finops import sustainability
from missions._common import catalog_by_type, load_csv, num

BASE_REGION = "us-east-1"


def run(verbose: bool = True) -> dict:
    """Giữ nguyên GPU-hours; chỉ thay giá điện và cường độ carbon của vùng."""
    catalog = catalog_by_type()
    jobs = []
    for row in load_csv("workloads.csv"):
        if int(num(row["interruptible"])) != 1:
            continue
        gpu_hours = num(row["hours_per_day"]) * num(row["days"]) * num(row["num_gpus"])
        wh = gpu_hours * num(catalog[row["gpu_type"]]["watts"])
        jobs.append({"job_id": row["job_id"], "gpu_hours": gpu_hours, "wh": wh})

    cleanest = min(sustainability.REGION_CARBON, key=sustainability.REGION_CARBON.get)
    cheapest = min(sustainability.REGION_PRICE_KWH, key=sustainability.REGION_PRICE_KWH.get)
    energy_wh = sum(job["wh"] for job in jobs)
    regions = []
    for region in sustainability.REGION_CARBON:
        regions.append({
            "region": region,
            "price_kwh": sustainability.REGION_PRICE_KWH[region],
            "carbon_kwh": sustainability.REGION_CARBON[region],
            "electricity_usd": sustainability.energy_cost_usd(energy_wh, region),
            "carbon_g": sustainability.carbon_g(energy_wh, region),
        })
    min_price = min(item["price_kwh"] for item in regions)
    max_price = max(item["price_kwh"] for item in regions)
    min_carbon = min(item["carbon_kwh"] for item in regions)
    max_carbon = max(item["carbon_kwh"] for item in regions)
    for item in regions:
        item["balanced_score"] = (
            (item["price_kwh"] - min_price) / (max_price - min_price)
            + (item["carbon_kwh"] - min_carbon) / (max_carbon - min_carbon)
        ) / 2
    balanced = min(regions, key=lambda item: item["balanced_score"])["region"]

    by_job = []
    for job in jobs:
        baseline_g = sustainability.carbon_g(job["wh"], BASE_REGION)
        clean_g = sustainability.carbon_g(job["wh"], cleanest)
        by_job.append({
            **job, "baseline_carbon_g": baseline_g, "clean_carbon_g": clean_g,
            "saved_carbon_g": baseline_g - clean_g,
        })
    result = {
        "base_region": BASE_REGION,
        "cleanest_region": cleanest,
        "cheapest_region": cheapest,
        "balanced_region": balanced,
        "jobs": by_job,
        "regions": regions,
        "total_wh": energy_wh,
        "saved_carbon_g": sum(job["saved_carbon_g"] for job in by_job),
    }
    if verbose:
        print("== Carbon-aware Scheduling ==")
        print("Job có thể gián đoạn; dùng đúng số ngày trong workloads.csv:")
        for job in by_job:
            print(f"{job['job_id']}: {job['baseline_carbon_g']:,.0f} -> "
                  f"{job['clean_carbon_g']:,.0f} gCO2e; giảm {job['saved_carbon_g']:,.0f} g")
        print("Vùng          USD/kWh  gCO2/kWh  tiền điện USD  gCO2e")
        for item in regions:
            print(f"{item['region']:17} {item['price_kwh']:>7.3f} {item['carbon_kwh']:>9} "
                  f"{item['electricity_usd']:>14,.2f} {item['carbon_g']:>12,.0f}")
        print(f"Rẻ điện nhất: {cheapest}; sạch nhất: {cleanest}; "
              f"cân bằng giá điện/carbon: {balanced}")
        print(f"Chuyển từ {BASE_REGION} sang {cleanest}: giảm {result['saved_carbon_g']:,.0f} gCO2e")
    return result


if __name__ == "__main__":
    run()
