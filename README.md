# 🎯 M/M/1 排队系统仿真分析

> 单服务台排队系统的离散事件仿真与可视化报告生成工具

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![SimPy](https://img.shields.io/badge/SimPy-4.1+-green?logo=simpy)
![Jinja2](https://img.shields.io/badge/Jinja2-3.1+-orange?logo=jinja)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4+-ff6384?logo=chartdotjs)

---

## 📖 项目简介

本项目使用 **离散事件仿真** 对 M/M/1 排队系统进行模拟，并将结果渲染为一份 **现代商务风 HTML 报告**（Dashboard 风格），包含数据表格、指标卡片和 Chart.js 交互图表。

适合用于 **排队论课程教学**、**运筹学实验报告** 或 **仿真方法入门**。

---

## 🧮 模型说明

| 符号 | 含义 | 本次取值 |
|------|------|---------|
| λ | 顾客到达率（泊松过程） | 3.0 |
| μ | 服务率（指数分布） | 4.0 |
| ρ = λ/μ | 系统负载（需 < 1 达到稳态） | **0.75** ✅ |

---

## 📁 项目结构

```
mm1-queueing-simulation/
│
├── mm1_simulation.py        ← M/M/1 仿真引擎（SimPy 实现）
├── render_report.py         ← 报告渲染脚本（运行仿真 + 生成 HTML）
├── templates/
│   └── report_template.html ← Jinja2 报告模板（CSS + Chart.js）
│
├── mm1_report.html          ← 生成的最终报告（可直接浏览器打开）
├── simulation_data.json     ← 仿真原始数据（备用）
├── 讲解稿件.md              ← 1-2 分钟讲解脚本
└── README.md
```

---

## 🚀 快速使用

### 1️⃣ 安装依赖

```bash
pip install simpy numpy jinja2
```

### 2️⃣ 生成报告（默认参数）

```bash
python render_report.py
```

### 3️⃣ 自定义参数

```bash
python render_report.py --lambda 3 --mu 4 --time 5000 --seed 42
```

参数说明：

| 参数 | 含义 | 默认值 |
|------|------|-------|
| `--lambda` | 到达率 λ | 3.0 |
| `--mu` | 服务率 μ | 4.0 |
| `--time` | 仿真时长 | 2000 |
| `--warmup` | 预热期 | 100 |
| `--seed` | 随机种子 | 42 |

> ⚠️ 需确保 **λ < μ**（即 ρ < 1），否则系统无法达到稳态。

### 4️⃣ 仅运行仿真（终端输出）

```bash
python mm1_simulation.py
```

---

## 📊 报告功能

| 模块 | 内容 |
|------|------|
| 🏷️ 模型简介 | M/M/1 排队模型背景说明 + 核心公式 |
| ⚙️ 参数展示 | λ、μ、ρ、仿真时长、顾客总数等 |
| 📈 KPI 指标卡片 | 等待时间 / 系统时间 / 队列长度 / 利用率（带进度条） |
| 📐 对比表 | 仿真值 vs 理论值 + 误差百分比 |
| ✅ Little's Law 验证 | Lq ≈ λ×Wq 守恒关系验证 |
| 📊 可视化图表 | 队列长度时序 / 等待时间分布 / 利用率时序 / 系统时间分布（4 张 Chart.js） |

**动画效果**：卡片浮入、进度条渐变、图表过渡动画，页面加载体验流畅。

---

## 🧪 仿真结果（示例）

| 指标 | 仿真值 | 理论值 | 误差 |
|------|-------|-------|------|
| 平均等待时间 Wq | 0.7006 | 0.7500 | 6.59% |
| 平均系统时间 W | 0.9500 | 1.0000 | 5.00% |
| 平均队列长度 Lq | 2.1112 | 2.2500 | 6.17% |
| 服务台利用率 ρ | **75.09%** | **75.00%** | **0.12%** ✅ |
| Little's Law 验证 | Lq ≈ λ×Wq | 差异 **0.45%** ✅ | |

---

## 🛠 技术栈

| 组件 | 用途 |
|------|------|
| [SimPy](https://simpy.readthedocs.io/) | 离散事件仿真引擎 |
| [NumPy](https://numpy.org/) | 数值计算 |
| [Jinja2](https://jinja.palletsprojects.com/) | HTML 模板渲染 |
| [Chart.js](https://www.chartjs.org/) | 前端交互图表 |
| CSS3 Animations | 页面入场动画 |
| Pure HTML + CSS | 无需服务器，直接浏览器打开 |

---

## 📚 参考资料

- [Queueing Theory (Wikipedia)](https://en.wikipedia.org/wiki/Queueing_theory)
- [SimPy Documentation](https://simpy.readthedocs.io/en/latest/)
- Kleinrock, L. *Queueing Systems, Vol. I: Theory*

---

## 📄 License

MIT
