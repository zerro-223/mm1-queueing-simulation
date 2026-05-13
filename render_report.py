"""
M/M/1 仿真报告渲染器
======================
运行仿真 → 加载模板 → 渲染数据 → 生成 HTML 报告。

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

from mm1_simulation import MM1Simulation, SimulationConfig, theoretical_values

# 尝试导入 Jinja2
try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("❌ 需要安装 Jinja2: pip install jinja2")
    sys.exit(1)


# ============================================================
# 主渲染函数
# ============================================================

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
    执行 M/M/1 仿真并生成 HTML 报告。

    Parameters
    ----------
    arrival_rate : float
        顾客到达率 λ
    service_rate : float
        服务率 μ
    sim_time : float
        仿真总时长
    warmup_time : float
        预热期（不计入统计）
    seed : int
        随机种子
    output_dir : str
        输出目录（默认当前脚本所在目录）
    template_dir : str
        模板目录（默认 output_dir/templates）

    Returns
    -------
    str
        生成的 HTML 文件路径
    """
    # ---- 确定路径 ----
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    if template_dir is None:
        template_dir = os.path.join(output_dir, "templates")

    os.makedirs(output_dir, exist_ok=True)

    # ---- 1. 运行仿真 ----
    print(f"\n{'='*60}")
    print(f"  M/M/1 排队系统仿真报告生成器")
    print(f"{'='*60}")
    print(f"\n  ⚙️  参数设置:")
    print(f"      λ (到达率)      = {arrival_rate}")
    print(f"      μ (服务率)      = {service_rate}")
    print(f"      ρ (负载)        = {arrival_rate/service_rate:.4f}")
    print(f"      仿真时长        = {sim_time}")
    print(f"      预热期          = {warmup_time}")
    print(f"      随机种子        = {seed}")
    print(f"\n  🚀 正在运行仿真...")

    config = SimulationConfig(
        arrival_rate=arrival_rate,
        service_rate=service_rate,
        sim_time=sim_time,
        warmup_time=warmup_time,
        seed=seed,
    )

    sim = MM1Simulation(config)
    result = sim.run()

    print(f"  ✅ 仿真完成!")
    print(f"     到达顾客: {result.total_customers}  完成服务: {result.customers_served}")

    # ---- 2. 准备数据 ----
    data = result.to_dict()
    theory = theoretical_values(config)

    # 添加额外渲染信息
    data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 转换时序数据为 JSON 字符串（Jinja2 模板中直接使用）
    data_for_template = {
        **data,
        "theoretical": theory,
        "queue_length_ts": json.dumps(data["queue_length_ts"]),
        "wait_times": json.dumps(data["wait_times"]),
        "system_times": json.dumps(data["system_times"]),
        "utilization_ts": json.dumps(data["utilization_ts"]),
    }

    # ---- 3. 渲染 HTML ----
    print(f"  🎨 渲染报告模板...")

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_template.html")

    html_content = template.render(
        data=data_for_template,
        theory=theory,
        **data_for_template,
    )

    # ---- 4. 保存文件 ----
    output_path = os.path.join(output_dir, "mm1_report.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_size = os.path.getsize(output_path)
    print(f"\n  📄 报告已生成: {output_path}")
    print(f"     文件大小: {file_size / 1024:.1f} KB")
    print(f"{'='*60}\n")

    return output_path


# ============================================================
# 命令行入口
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="M/M/1 排队系统仿真报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python render_report.py
    python render_report.py --lambda 5 --mu 6 --time 3000
    python render_report.py --lambda 2 --mu 5 --time 5000 --seed 123
        """
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

    # 验证 ρ < 1
    rho = args.arrival_rate / args.service_rate
    if rho >= 1:
        print(f"\n  ❌ 错误: ρ = {rho:.4f} >= 1，系统无法达到稳态!")
        print(f"     请调整参数使 λ < μ (即 ρ < 1)。\n")
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
