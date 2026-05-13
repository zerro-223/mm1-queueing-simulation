"""
M/M/1 排队系统离散事件仿真
================================
使用 SimPy 库实现 M/M/1 排队模型。

模型参数:
    λ (lambda) : 顾客到达率 (arrival rate)
    μ (mu)     : 服务率 (service rate)
    ρ = λ/μ   : 系统负载 (traffic intensity), 需要 ρ < 1 以保证稳态

收集的性能指标:
    - 平均等待时间 (Average Waiting Time)
    - 平均队列长度 (Average Queue Length)
    - 服务台利用率 (Server Utilization)
    - 系统平均逗留时间 (Average System Time)
"""

import simpy
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
import random


# ============================================================
# 数据容器
# ============================================================

@dataclass
class SimulationConfig:
    """仿真配置参数"""
    arrival_rate: float       # λ — 到达率（顾客/时间单位）
    service_rate: float       # μ — 服务率（顾客/时间单位）
    sim_time: float = 1000.0  # 仿真总时长
    warmup_time: float = 50.0 # 预热期（不计入统计，消除初始偏差）
    seed: Optional[int] = 42  # 随机种子，保证可重复性

    @property
    def rho(self) -> float:
        """系统负载 ρ = λ / μ"""
        return self.arrival_rate / self.service_rate

    @property
    def inter_arrival_time(self) -> float:
        """平均到达间隔时间 1/λ"""
        return 1.0 / self.arrival_rate

    @property
    def service_time_mean(self) -> float:
        """平均服务时间 1/μ"""
        return 1.0 / self.service_rate


@dataclass
class CustomerRecord:
    """单个顾客的记录数据"""
    customer_id: int
    arrival_time: float
    service_start_time: Optional[float] = None
    departure_time: Optional[float] = None

    @property
    def waiting_time(self) -> float:
        """等待时间 = 服务开始 - 到达"""
        if self.service_start_time is not None and self.arrival_time is not None:
            return self.service_start_time - self.arrival_time
        return 0.0

    @property
    def system_time(self) -> float:
        """系统逗留时间 = 离开 - 到达"""
        if self.departure_time is not None and self.arrival_time is not None:
            return self.departure_time - self.arrival_time
        return 0.0

    @property
    def service_duration(self) -> float:
        """服务持续时间 = 离开 - 服务开始"""
        if self.departure_time is not None and self.service_start_time is not None:
            return self.departure_time - self.service_start_time
        return 0.0


@dataclass
class SimulationResult:
    """仿真结果汇总"""
    config: SimulationConfig
    total_customers: int = 0
    customers_served: int = 0
    records: List[CustomerRecord] = field(default_factory=list)
    queue_length_over_time: List[tuple] = field(default_factory=list)
    server_busy_over_time: List[tuple] = field(default_factory=list)

    # ---- 计算指标 ----

    @property
    def avg_waiting_time(self) -> float:
        """平均等待时间 Wq"""
        if not self.records:
            return 0.0
        return np.mean([r.waiting_time for r in self.records])

    @property
    def avg_system_time(self) -> float:
        """平均系统逗留时间 W"""
        if not self.records:
            return 0.0
        return np.mean([r.system_time for r in self.records])

    @property
    def avg_queue_length(self) -> float:
        """平均队列长度 Lq (以时间为权重)"""
        if not self.queue_length_over_time:
            return 0.0
        return self._time_weighted_average(self.queue_length_over_time)

    @property
    def server_utilization(self) -> float:
        """服务台利用率 = 忙碌时间 / 总时间"""
        if not self.server_busy_over_time:
            return 0.0
        return self._time_weighted_average(
            self.server_busy_over_time,
            value_extractor=lambda v: 0.0 if v else 1.0,
            # server_busy 中 True=空闲, False=忙碌
            # 忙碌时贡献 1.0，空闲时贡献 0.0
        )

    @property
    def avg_customers_in_system(self) -> float:
        """系统中平均顾客数 L = λ * W (Little's Law 验证)"""
        return self.avg_queue_length + self.server_utilization

    # Little's Law 验证
    @property
    def littles_law_wait(self) -> float:
        """Little's Law Wq ≈ Lq / λ"""
        effective_lambda = self.config.arrival_rate
        if effective_lambda == 0:
            return 0.0
        return self.avg_queue_length / effective_lambda

    @property
    def littles_law_system(self) -> float:
        """Little's Law W ≈ L / λ"""
        effective_lambda = self.config.arrival_rate
        if effective_lambda == 0:
            return 0.0
        return self.avg_customers_in_system / effective_lambda

    @staticmethod
    def _time_weighted_average(data: List[tuple],
                                value_extractor=None) -> float:
        """计算时间加权平均值"""
        if not data:
            return 0.0
        total_value_time = 0.0
        total_time = 0.0
        for i in range(1, len(data)):
            t_prev, v_prev = data[i - 1]
            t_curr, v_curr = data[i]
            dt = t_curr - t_prev
            val = value_extractor(v_prev) if value_extractor else v_prev
            total_value_time += val * dt
            total_time += dt
        return total_value_time / total_time if total_time > 0 else 0.0

    def to_dict(self) -> dict:
        """序列化为字典，供模板渲染使用"""
        return {
            # 模型参数
            "arrival_rate": self.config.arrival_rate,
            "service_rate": self.config.service_rate,
            "rho": self.config.rho,
            "arrival_interval": round(self.config.inter_arrival_time, 4),
            "service_time_mean": round(self.config.service_time_mean, 4),
            "sim_time": self.config.sim_time,
            "warmup_time": self.config.warmup_time,
            "seed": self.config.seed,
            "total_customers": self.total_customers,
            "customers_served": self.customers_served,
            # 性能指标
            "avg_waiting_time": round(self.avg_waiting_time, 4),
            "avg_system_time": round(self.avg_system_time, 4),
            "avg_queue_length": round(self.avg_queue_length, 4),
            "server_utilization": round(self.server_utilization, 4),
            "avg_customers_in_system": round(self.avg_customers_in_system, 4),
            # Little's Law 验证
            "littles_law_wq": round(self.littles_law_wait, 4),
            "littles_law_w": round(self.littles_law_system, 4),
            "wq_diff_pct": round(
                abs(self.avg_waiting_time - self.littles_law_wait)
                / self.avg_waiting_time * 100
                if self.avg_waiting_time > 0 else 0, 2
            ),
            # 分位数
            "wait_quantile_50": round(np.quantile([r.waiting_time for r in self.records], 0.50), 4) if self.records else 0,
            "wait_quantile_90": round(np.quantile([r.waiting_time for r in self.records], 0.90), 4) if self.records else 0,
            "wait_quantile_99": round(np.quantile([r.waiting_time for r in self.records], 0.99), 4) if self.records else 0,
            "wait_max": round(max((r.waiting_time for r in self.records), default=0), 4),
            # 队列长度时序数据（采样用于图表）
            "queue_length_ts": [
                {"t": round(t, 2), "v": int(v)}
                for t, v in self.queue_length_over_time
            ],
            # 统计分布数据（用于直方图）
            "wait_times": [round(r.waiting_time, 4) for r in self.records],
            "system_times": [round(r.system_time, 4) for r in self.records],
            "service_times": [round(r.service_duration, 4) for r in self.records],
            # 服务台利用率时序
            "utilization_ts": [
                {"t": round(t, 2), "v": 0 if v else 1}
                for t, v in self.server_busy_over_time
            ],
        }


# ============================================================
# M/M/1 仿真核心
# ============================================================

class MM1Simulation:
    """
    M/M/1 排队系统仿真器

    使用 SimPy 的离散事件引擎模拟：
    - 到达过程：顾客按照泊松过程到达（指数间隔）
    - 服务过程：服务时间服从指数分布
    - 排队规则：FIFO（先到先服务）
    - 服务台：单个服务台
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.env = simpy.Environment()
        self.server = simpy.Resource(self.env, capacity=1)

        # 数据收集器
        self.records: List[CustomerRecord] = []
        self.customer_counter = 0

        # 用于时间加权统计
        self.queue_length_ts: List[tuple] = [(0.0, 0)]
        self.server_busy_ts: List[tuple] = [(0.0, True)]  # True=空闲, False=忙

        self._total_arrivals = 0
        self._total_served = 0

        # 设置随机种子
        random.seed(config.seed)
        np.random.seed(config.seed)

    def run(self) -> SimulationResult:
        """运行仿真并返回结果"""
        # 启动到达过程
        self.env.process(self._arrival_process())

        # 启动定时采样器
        self.env.process(self._sampler())

        # 运行仿真
        self.env.run(until=self.config.sim_time)

        # 构造结果
        warmup_end = self.config.warmup_time
        valid_records = [r for r in self.records
                         if r.arrival_time >= warmup_end]

        result = SimulationResult(
            config=self.config,
            total_customers=self._total_arrivals,
            customers_served=self._total_served,
            records=valid_records,
            queue_length_over_time=[
                (t, q) for t, q in self.queue_length_ts
                if t >= warmup_end
            ],
            server_busy_over_time=[
                (t, b) for t, b in self.server_busy_ts
                if t >= warmup_end
            ],
        )
        return result

    def _arrival_process(self):
        """顾客到达过程——泊松到达"""
        while True:
            # 生成指数分布的到达间隔
            inter_arrival = random.expovariate(self.config.arrival_rate)
            yield self.env.timeout(inter_arrival)

            self.customer_counter += 1
            self._total_arrivals += 1
            arrival_time = self.env.now

            # 创建顾客记录并开始服务流程
            record = CustomerRecord(
                customer_id=self.customer_counter,
                arrival_time=arrival_time,
            )
            self.records.append(record)
            self.env.process(self._service_process(record))

    def _service_process(self, record: CustomerRecord):
        """单个顾客的服务流程"""
        # 请求服务台
        with self.server.request() as request:
            yield request

            # 记录服务开始时间
            record.service_start_time = self.env.now

            # 生成指数分布的服务时间
            service_time = random.expovariate(self.config.service_rate)
            yield self.env.timeout(service_time)

            # 记录离开时间
            record.departure_time = self.env.now
            self._total_served += 1

    def _sampler(self):
        """定期采样系统的队列长度和服务台状态"""
        while True:
            yield self.env.timeout(0.1)  # 每 0.1 时间单位采样一次

            # 队列长度 = 等待队列中的人数（在服务中的人数不计入队列）
            queue_len = len(self.server.queue)
            self.queue_length_ts.append((self.env.now, queue_len))

            # 服务台状态：True=空闲, False=忙碌
            is_idle = self.server.count == 0
            self.server_busy_ts.append((self.env.now, is_idle))


# ============================================================
# 理论值计算
# ============================================================

def theoretical_values(config: SimulationConfig) -> dict:
    """
    计算 M/M/1 排队系统的理论值。

    公式:
        L  = ρ / (1 - ρ)           # 系统中平均顾客数
        Lq = ρ² / (1 - ρ)           # 平均队列长度
        W  = 1 / (μ - λ)            # 平均系统时间
        Wq = ρ / (μ - λ)            # 平均等待时间
        P0 = 1 - ρ                  # 系统空闲概率
        U  = ρ                      # 服务台利用率
    """
    lam = config.arrival_rate
    mu = config.service_rate
    rho = config.rho

    L = rho / (1 - rho)
    Lq = rho ** 2 / (1 - rho)
    W = 1.0 / (mu - lam)
    Wq = rho / (mu - lam)
    P0 = 1 - rho
    U = rho

    return {
        "L": round(L, 4),
        "Lq": round(Lq, 4),
        "W": round(W, 4),
        "Wq": round(Wq, 4),
        "P0": round(P0, 4),
        "U": round(U, 4),
    }


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    import json

    # ---- 配置参数 ----
    config = SimulationConfig(
        arrival_rate=3.0,    # λ = 3 个顾客/时间单位
        service_rate=4.0,    # μ = 4 个顾客/时间单位
        sim_time=2000.0,     # 仿真时长
        warmup_time=100.0,   # 预热期
        seed=42,
    )

    print("=" * 60)
    print("  M/M/1 排队系统仿真")
    print("=" * 60)
    print(f"\n  配置参数:")
    print(f"    λ (到达率)  = {config.arrival_rate}")
    print(f"    μ (服务率)  = {config.service_rate}")
    print(f"    ρ (负载)    = {config.rho:.4f}")
    print(f"    仿真时长    = {config.sim_time}")
    print(f"    预热期      = {config.warmup_time}")
    print(f"    随机种子    = {config.seed}")

    # ---- 运行仿真 ----
    print(f"\n  正在仿真中...")
    sim = MM1Simulation(config)
    result = sim.run()

    # ---- 理论值 ----
    theo = theoretical_values(config)

    # ---- 输出结果 ----
    print(f"\n  {'='*50}")
    print(f"  📊 仿真结果")
    print(f"  {'='*50}")
    print(f"    到达顾客数    : {result.total_customers}")
    print(f"    完成服务数    : {result.customers_served}")
    print(f"  {'─'*50}")
    print(f"  性能指标         仿真值         理论值       误差(%)")
    print(f"  {'─'*50}")
    print(f"  平均等待时间 Wq  {result.avg_waiting_time:<10.4f}  {theo['Wq']:<10.4f}  "
          f"{abs(result.avg_waiting_time - theo['Wq'])/theo['Wq']*100:>6.2f}%")
    print(f"  平均系统时间 W   {result.avg_system_time:<10.4f}  {theo['W']:<10.4f}  "
          f"{abs(result.avg_system_time - theo['W'])/theo['W']*100:>6.2f}%")
    print(f"  平均队列长度 Lq  {result.avg_queue_length:<10.4f}  {theo['Lq']:<10.4f}  "
          f"{abs(result.avg_queue_length - theo['Lq'])/theo['Lq']*100:>6.2f}%")
    print(f"  利用率 ρ         {result.server_utilization:<10.4f}  {theo['U']:<10.4f}  "
          f"{abs(result.server_utilization - theo['U'])/theo['U']*100:>6.2f}%")

    # ---- Little's Law 验证 ----
    print(f"\n  {'─'*50}")
    print(f"  📐 Little's Law 验证")
    print(f"  {'─'*50}")
    print(f"    Lq ≈ λ×Wq : {result.avg_queue_length:.4f} ≈ "
          f"{result.littles_law_wait:.4f}  (差异 {result.to_dict()['wq_diff_pct']:.2f}%)")
    print(f"    Wq  ≈ Lq/λ : {result.avg_waiting_time:.4f} ≈ "
          f"{result.littles_law_wait:.4f}")
    print(f"  {'='*50}")

    # ---- 输出 JSON 数据供渲染使用 ----
    data = result.to_dict()
    data["theoretical"] = theo
    print(f"\n  JSON 数据已准备好，共 {result.customers_served} 条记录。\n")

    # 保存 JSON 数据到文件
    with open("simulation_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 仿真数据已保存至 simulation_data.json")
