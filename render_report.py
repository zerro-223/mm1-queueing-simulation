"""
M/M/1 仿真报告渲染器
======================
运行仿真 → 多维度数据分析 → 渲染 HTML 报告。

使用方法:
    python render_report.py                  # 默认参数
    python render_report.py --lambda 3 --mu 4 --time 2000 --seed 42
"""

import sys
import os
import json
from datetime import datetime

# 确保能导入同目录的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mm1_simulation import (
    MM1Simulation, SimulationConfig, theoretical_values,
    system_state_probability, waiting_time_distribution,
    run_batch_simulations, convergence_analysis,
)

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("❌ 需要安装 Jinja2: pip install jinja2")
    sys.exit(1)


def render_report(
    arrival_rate: float = 3.0,
    service_rate: float = 4.0,
    sim_time: float = 2000.0,
    warmup_time: float = 100.0,
    seed: int = 42,
    output_dir: str = None,
    template_dir: str = None,
) -> str:
    """
    执行 M/M/1 仿真、多维度分析，并生成 HTML 报告。
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    if template_dir is None:
        template_dir = os.path.join(output_dir, "templates")

    os.makedirs(output_dir, exist_ok=True)

    # ============================================================
    # 1. 主仿真
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  M/M/1 排队系统仿真报告生成器")
    print(f"{'='*60}")
    print(f"\n  ⚙️  参数设置:")
    print(f"      λ (到达率)      = {arrival_rate}")
    print(f"      μ (服务率)      = {service_rate}")
    print(f"      ρ (负载)        = {arrival_rate/service_rate:.4f}")
    print(f"      仿真时长        = {sim_time}")
    print(f"      预热期          = {warmup_time}")

    config = SimulationConfig(
        arrival_rate=arrival_rate,
        service_rate=service_rate,
        sim_time=sim_time,
        warmup_time=warmup_time,
        seed=seed,
    )

    print(f"\n  🚀 正在运行主仿真...")
    sim = MM1Simulation(config)
    result = sim.run()
    print(f"  ✅ 主仿真完成! 到达: {result.total_customers}  服务: {result.customers_served}")

    data = result.to_dict()
    theory = theoretical_values(config)
    data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ============================================================
    # 2. 系统状态概率分析
    # ============================================================
    print(f"  📊 正在分析系统状态概率分布...")
    state_prob = system_state_probability(result, config, max_n=10)

    # ============================================================
    # 3. 等待时间分布分析
    # ============================================================
    print(f"  📈 正在分析等待时间分布...")
    wait_dist = waiting_time_distribution(result, config, num_points=60)

    # ============================================================
    # 4. 负载敏感性分析（多 ρ 批量仿真）
    # ============================================================
    print(f"  🔬 正在运行灵敏度分析（多 ρ 值）...")
    rho_values = [0.3, 0.5, 0.7, 0.8, 0.85, 0.9, 0.95]
    sensitivity = run_batch_simulations(
        rhos=rho_values,
        mu=service_rate,
        sim_time=min(sim_time, 3000),
        warmup_time=min(warmup_time, 200),
        seed=seed,
    )

    # ============================================================
    # 5. 收敛性分析
    # ============================================================
    print(f"  📉 正在分析仿真收敛性...")
    convergence = convergence_analysis(
        base_config=config,
        sim_times=[100, 300, 500, 1000, 2000, 5000, 10000],
    )

    # ============================================================
    # 6. 实际意义解读
    # ============================================================
    # 计算一些可读性强的分析结论
    rho = config.rho
    lam = arrival_rate
    mu = service_rate
    Wq_sim = result.avg_waiting_time
    W_sim = result.avg_system_time
    Lq_sim = result.avg_queue_length

    # 如果利用率从 ρ 升到 ρ+0.1，等待时间变化倍数
    higher_rho = min(rho + 0.1, 0.98)
    if rho < 0.98:
        wq_growth = (higher_rho / (1 - higher_rho)) / (rho / (1 - rho))
    else:
        wq_growth = 0

    # 单位时间顾客数与等待时间的关系
    waiting_times_array = [r.waiting_time for r in result.records]
    pct_waiting_over_1 = sum(1 for w in waiting_times_array if w > 1.0) / max(len(waiting_times_array), 1) * 100
    pct_waiting_over_2 = sum(1 for w in waiting_times_array if w > 2.0) / max(len(waiting_times_array), 1) * 100

    # 理论空闲概率
    p0 = 1 - rho

    interpretation = {
        "rho": rho,
        "formatted_rho": f"{rho:.1%}",
        "p0": p0,
        "formatted_p0": f"{p0:.1%}",
        "pct_waiting_over_1": round(pct_waiting_over_1, 1),
        "pct_waiting_over_2": round(pct_waiting_over_2, 1),
        "wq_growth_if_rho_plus_01": round(wq_growth, 2) if wq_growth > 0 else None,
        "higher_rho": round(higher_rho, 2),
        "arrivals_per_unit": lam,
        "service_rate": mu,
        "avg_wait": round(Wq_sim, 4),
        "avg_system_time": round(W_sim, 4),
        "avg_queue": round(Lq_sim, 2),
        # 直观解读：平均每 λ 时间单位来一个顾客
        "arrival_interval": round(1 / lam, 2),
        "service_time": round(1 / mu, 2),
        # 系统效率评分
        "efficiency": "低负载 · 快速响应" if rho < 0.5 else
                      "中等负载 · 运行良好" if rho < 0.7 else
                      "高负载 · 接近容量极限" if rho < 0.9 else
                      "极高负载 · 接近不稳定",
    }

    # ============================================================
    # 7. 组装模板数据
    # ============================================================
    data_for_template = {
        **data,
        "theoretical": theory,
        "queue_length_ts": json.dumps(data["queue_length_ts"]),
        "wait_times": json.dumps(data["wait_times"]),
        "system_times": json.dumps(data["system_times"]),
        "utilization_ts": json.dumps(data["utilization_ts"]),
        # 分析数据
        "state_prob": json.dumps(state_prob),
        "wait_dist": json.dumps(wait_dist),
        "sensitivity": json.dumps(sensitivity),
        "convergence": json.dumps(convergence),
        "sensitivity_raw": sensitivity,
        "convergence_raw": convergence,
        "interpretation": interpretation,
    }

    # ============================================================
    # 8. 渲染 HTML
    # ============================================================
    print(f"  🎨 渲染报告模板...")

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_template.html")

    html_content = template.render(
        data=data_for_template,
        theory=theory,
        **data_for_template,
    )

    output_path = os.path.join(output_dir, "mm1_report.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_size = os.path.getsize(output_path)
    print(f"\n  📄 报告已生成: {output_path}")
    print(f"     文件大小: {file_size / 1024:.1f} KB")
    print(f"{'='*60}\n")

    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="M/M/1 排队系统仿真报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--lambda", dest="arrival_rate", type=float, default=3.0,
                        help="顾客到达率 λ (默认: 3.0)")
    parser.add_argument("--mu", dest="service_rate", type=float, default=4.0,
                        help="服务率 μ (默认: 4.0)")
    parser.add_argument("--time", dest="sim_time", type=float, default=2000.0,
                        help="仿真总时长 (默认: 2000)")
    parser.add_argument("--warmup", dest="warmup_time", type=float, default=100.0,
                        help="预热期时长 (默认: 100)")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子 (默认: 42)")
    parser.add_argument("--output", dest="output_dir", type=str, default=None,
                        help="输出目录 (默认: 当前目录)")

    args = parser.parse_args()

    rho = args.arrival_rate / args.service_rate
    if rho >= 1:
        print(f"\n  ❌ 错误: ρ = {rho:.4f} >= 1，系统无法达到稳态!")
        sys.exit(1)

    render_report(
        arrival_rate=args.arrival_rate,
        service_rate=args.service_rate,
        sim_time=args.sim_time,
        warmup_time=args.warmup_time,
        seed=args.seed,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
