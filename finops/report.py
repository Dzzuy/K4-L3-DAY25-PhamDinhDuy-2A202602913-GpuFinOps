"""Report assembly — the lab's deliverable: baseline vs optimized + savings chart."""
from __future__ import annotations


def build_report(baseline_usd: float, optimized_usd: float, levers: dict,
                 sustainability: dict | None = None, period: str = "monthly",
                 inference: dict | None = None, analysis: dict | None = None,
                 reasoning: dict | None = None, carbon_schedule: dict | None = None) -> str:
    """Return a markdown cost-optimization report."""
    savings = baseline_usd - optimized_usd
    pct = (savings / baseline_usd * 100.0) if baseline_usd > 0 else 0.0
    lines = [
        "# NimbusAI — Báo cáo tối ưu chi phí GPU",
        "",
        f"**Kỳ tính:** {period}",
        "",
        f"**Chi phí ban đầu (baseline):** ${baseline_usd:,.0f}",
        "",
        f"**Chi phí sau tối ưu:** ${optimized_usd:,.0f}",
        "",
        f"**Projected savings (tiết kiệm dự kiến):** ${savings:,.0f} ({pct:.0f}%)",
        "",
        "## Tiết kiệm theo từng cách",
        "",
        "| Cách làm | Tiết kiệm (USD/tháng) |",
        "|---|---|",
    ]
    for name, amount in levers.items():
        lines.append(f"| {name} | ${amount:,.0f} |")
    if inference:
        lines += [
            "",
            "## Chi phí inference trên mỗi triệu token",
            "",
            f"Cùng {inference['total_tokens']:,} token/ngày: baseline **${inference['baseline_per_m']:.3f}/1M-token**, sau tối ưu **${inference['optimized_per_m']:.3f}/1M-token**.",
            "Phần tiết kiệm được tính lần lượt theo cascade → cache → batch, nên không đếm trùng chiết khấu:",
            "",
            "| Cách làm | Tiết kiệm (USD/tháng) |",
            "|---|---:|",
        ]
        for name, amount in inference["lever_savings_monthly"].items():
            lines.append(f"| {name} | ${amount:,.2f} |")
    if analysis:
        lines += [
            "",
            "## Nhận xét và việc cần làm",
            "",
            f"- GPU-Util lie: {analysis['lie_summary']}. GPU-Util đo mức bận, còn MFU đo FLOPs hữu ích. MBU thấp có thể gợi ý nghẽn bộ nhớ; cần profile thêm trước khi kết luận nguyên nhân và đổi GPU.",
            f"- Ưu tiên 1: kiểm tra chính sách spot/reserved cho workload đủ điều kiện (tiết kiệm khoảng ${levers['Purchasing (spot/reserved)']:,.0f}/tháng); xác nhận khả năng checkpoint và thời hạn cam kết.",
            f"- Ưu tiên 2: áp dụng cascade trước, rồi cache và batch cho request chấp nhận chờ (tiết kiệm khoảng ${levers['Inference (cascade/cache/batch)']:,.0f}/tháng); theo dõi chất lượng và độ trễ.",
            f"- Ưu tiên 3: tắt GPU idle (khoảng ${levers['Kill idle GPUs']:,.0f}/tháng), sau đó thử right-size trên workload có MFU thấp và đo lại throughput.",
            "- Các khoản trên là ước tính từ mô phỏng. M3 dùng 30 ngày cho mọi job; right-size giả định giữ nguyên throughput và không cộng thêm chi phí chuyển đổi.",
        ]
    if reasoning:
        normal = reasoning["normal"]
        deep = reasoning["reasoning"]
        total_requests = normal["requests"] + deep["requests"]
        total_cost = normal["cost_daily"] + deep["cost_daily"]
        total_wh = normal["wh_daily"] + deep["wh_daily"]
        lines += [
            "",
            "## Ngân sách reasoning (mở rộng)",
            "",
            "| Nhóm | Request/ngày | Token/ngày | USD/ngày | Wh/ngày |",
            "|---|---:|---:|---:|---:|",
            f"| Thường | {normal['requests']:,} | {normal['tokens']:,} | ${normal['cost_daily']:.2f} | {normal['wh_daily']:.1f} |",
            f"| Reasoning | {deep['requests']:,} | {deep['tokens']:,} | ${deep['cost_daily']:.2f} | {deep['wh_daily']:.1f} |",
            "",
            f"Trong {total_requests:,} request, có {deep['requests']} request bật reasoning. "
            f"Nhóm này chiếm {deep['requests'] / total_requests:.1%} lượt dùng, "
            f"{deep['cost_daily'] / total_cost:.1%} tiền và {deep['wh_daily'] / total_wh:.1%} điện năng. "
            "Bảng giá của bài lab không tính thêm phí reasoning; tiền khác nhau do số token và model được chọn. "
            "Mức điện năng gấp 80 lần là giả định của bài, chưa phải số đo trên GPU thật.",
            "",
            "Chỉ bật reasoning cho việc nhiều bước mà cách xử lý thường không đạt chất lượng. "
            "Nếu vượt giới hạn, chuyển bớt sang model nhỏ rồi kiểm tra lại câu trả lời.",
            "",
        ]
        for key in ("cap_10", "cap_5"):
            scenario = reasoning[key]
            lines.append(
                f"- Cap {scenario['cap_pct']:.0f}% traffic: chuyển {scenario['rerouted']} request/ngày; "
                f"chi phí ${total_cost:.2f} → ${total_cost - scenario['cost_saved_daily']:.2f}/ngày, "
                f"điện năng {total_wh:.1f} → {total_wh - scenario['wh_saved_daily']:.1f} Wh/ngày."
            )
        lines.append("")
        lines.append(
            "Ở mức 5%, mình chuyển các request nhiều token nhất trước. "
            "Tiền chỉ giảm khi request đang dùng model lớn được chuyển sang model nhỏ. "
            "Đây là phép tính thử; chưa biết chất lượng câu trả lời sẽ đổi ra sao."
        )
    if sustainability:
        lines += [
            "",
            "## Sustainability",
            "",
            f"- Truy vấn mẫu {sustainability['sample_tokens']} token: {sustainability['wh_per_query']:.2f} Wh, phát thải {sustainability['carbon_g']:.3f} gCO2e tại {sustainability['base_region']}.",
            f"- Tiền điện tại {sustainability['base_region']}: ${sustainability['base_energy_usd']:.6f}/truy vấn; tại vùng sạch nhất {sustainability['cleanest_region']}: ${sustainability['clean_energy_usd']:.6f}/truy vấn và {sustainability['clean_carbon_g']:.3f} gCO2e.",
            f"- Vùng có điện rẻ nhất: {sustainability['cheapest_region']}; vùng sạch nhất: {sustainability['cleanest_region']}. Chọn vùng triển khai còn phải xét độ trễ và chi phí hạ tầng; các giá điện là giả định minh họa.",
        ]
    if carbon_schedule:
        lines += [
            "",
            "## Chuyển job sang vùng ít phát thải (mở rộng)",
            "",
            "Chỉ tính các job có thể gián đoạn. Mỗi job dùng đúng số ngày trong `workloads.csv`; "
            "giữ nguyên GPU và số giờ chạy, chỉ thay vùng đặt máy.",
            "",
            "| Job | gCO₂e tại us-east-1 | gCO₂e tại vùng sạch nhất | Giảm gCO₂e |",
            "|---|---:|---:|---:|",
        ]
        for job in carbon_schedule["jobs"]:
            lines.append(
                f"| {job['job_id']} | {job['baseline_carbon_g']:,.0f} | "
                f"{job['clean_carbon_g']:,.0f} | {job['saved_carbon_g']:,.0f} |"
            )
        lines += [
            "",
            "| Vùng | USD/kWh | gCO₂/kWh | Tiền điện USD | gCO₂e |",
            "|---|---:|---:|---:|---:|",
        ]
        for region in carbon_schedule["regions"]:
            lines.append(
                f"| {region['region']} | {region['price_kwh']:.3f} | "
                f"{region['carbon_kwh']} | ${region['electricity_usd']:,.2f} | "
                f"{region['carbon_g']:,.0f} |"
            )
        lines += [
            "",
            f"Chuyển toàn bộ job trên từ {carbon_schedule['base_region']} sang "
            f"{carbon_schedule['cleanest_region']} giảm khoảng "
            f"{carbon_schedule['saved_carbon_g']:,.0f} gCO₂e. "
            f"{carbon_schedule['cheapest_region']} rẻ điện nhất; "
            f"{carbon_schedule['cleanest_region']} ít phát thải nhất. "
            f"Nếu coi giá điện và carbon quan trọng ngang nhau, {carbon_schedule['balanced_region']} "
            "có điểm cân bằng tốt nhất trong năm vùng. Chưa tính độ trễ, giá thuê GPU và phí chuyển dữ liệu; "
            "cần kiểm tra các khoản đó trước khi chuyển job thật.",
        ]
    lines += ["", "_Giá và cường độ carbon là số liệu minh họa tại tháng 6/2026; cần cập nhật trước khi áp dụng thực tế._"]
    return "\n".join(lines)


def savings_waterfall(levers: dict, path: str) -> str:
    """Write a simple savings bar chart PNG. Returns the path. No-op if matplotlib absent."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    names = list(levers.keys())
    vals = [levers[n] for n in names]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    remaining = sum(vals)
    for name, value in zip(names, vals):
        remaining -= value
        ax.bar(name, value, bottom=remaining, color="#2e548a")
        ax.annotate(f"${value:,.0f}", (name, remaining + value),
                    xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8)
    ax.set_ylabel("USD tiết kiệm / tháng")
    ax.set_title("Các khoản tiết kiệm chi phí GPU")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
