<div align="center">

<img src="docs/banner.svg" alt="LifeTrace Banner" width="100%" />

# LifeTrace

### Personal Life Data Observatory · 人生轨迹实验室

**一套「个人行为数据实验室」——不是记账、待办或打卡软件，而是把每天的生活数据变成一条可读、可分析、可理解的时间序列。**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4%2B-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.20%2B-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![Tests](https://img.shields.io/badge/Tests-28%20passed-10B981?logo=pytest&logoColor=white)](./tests)

**本地运行 · 零云依赖 · 数据完全私有**

</div>

---

## 这是什么

LifeTrace 是一个**个人生活数据分析与可视化系统**。你每天花一分钟录入少量生活数据（睡眠、学习、运动、社交、消费、心情、压力……），系统会自动把它们整理成个人时间序列，并用**真正的统计方法**（而非简单柱状图）帮你理解自己的生活规律：

- 睡眠如何影响心情？
- 学习时长和压力有什么关系？
- 哪些日子是"高效率日"、哪些是"恢复日"？
- 最近哪几天和你的历史行为明显不一样？

所有的洞察都由你自己的数据驱动，并以**证据式、非诊断性**的语言呈现。

---

## 界面截图

| 概览 Dashboard | 分析 Analysis |
| :---: | :---: |
| ![概览](screenshots/dashboard.png) | ![分析](screenshots/analysis.png) |

| 数据录入 Record | 数据管理 Data |
| :---: | :---: |
| ![记录](screenshots/record.png) | ![数据](screenshots/data.png) |

> 截图由 `scripts/screenshot.py` 通过无头浏览器自动生成。

---

## 核心功能

### 📊 个人 Dashboard
首页是一个现代数据产品风格的看板：今日状态、本周 / 本月统计、平均睡眠、平均学习、平均心情、运动次数、消费趋势、计划完成率、连续记录天数、数据异常提醒。

### 🔬 真正的统计分析（不是画图而已）

| 功能 | 方法 | 说明 |
|------|------|------|
| 相关性分析 | Pearson r + p 值 | 睡眠×心情、睡眠×学习、运动×心情、社交×心情、消费×压力；点击任意组合查看散点图 |
| 时间序列分析 | 移动平均 | 日 / 周 / 月三种粒度，含 7 日移动平均线，可切换指标 |
| 异常检测 | Isolation Forest + z-score | 找出与你历史行为明显不同的日期，并给出证据式解释 |
| 生活模式聚类 | K-Means（轮廓系数选 k） | 自动形成"高效率日 / 低能量日 / 社交日 / 恢复日"等，**名称由数据特征决定** |
| 个人效率模型 | 线性回归 | 预测当天"状态评分"，输出特征重要性 |

### ✨ 特色功能：如果我改变一个变量，会发生什么？

选择"睡眠从 5 小时提高到 7 小时"，系统基于历史中**相似日期的匹配估计**告诉你：

> 在你的历史数据中，与 7 小时睡眠相似的日期，平均学习时间提高约 X%，平均心情提高约 X 分。

并始终明确标注：**这是基于历史相关数据的估计，不代表因果关系。**

### 📥 数据导入导出
支持 CSV 导入 / CSV 导出 / JSON 导出 / 数据库备份。首次运行自动生成 60 天**真实感** Demo 数据（工作日学习多、周末睡眠长、考试周压力升、连续熬夜后效率下降、偶发消费异常），打开项目即可看到完整效果。

---

## 技术栈

| 层 | 技术 |
|----|------|
| Web 框架 | FastAPI + Uvicorn |
| 数据库 | SQLite（默认）+ SQLAlchemy ORM |
| 数据处理 | Pandas + NumPy |
| 统计 / 机器学习 | SciPy + scikit-learn |
| 可视化 | Plotly |
| 模板 | Jinja2（纯服务端渲染 + 原生 JS，无需 Node.js） |

---

## 快速开始

### 环境要求

- Python **3.11+**

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/<your-username>/LifeTrace.git
cd LifeTrace

# 2.（可选但推荐）创建虚拟环境
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
python run.py
```

打开浏览器访问 **http://127.0.0.1:8000**。

首次启动时，若数据库为空，系统会自动生成 60 天 Demo 数据，让你立刻看到完整效果。你也可以手动生成或重置 Demo 数据：

```bash
python scripts/generate_demo_data.py --days 90 --reset
```

---

## 项目结构

```
LifeTrace/
├── app/                      # 应用核心
│   ├── main.py               # FastAPI 入口
│   ├── config.py             # 配置（路径、数据库 URL）
│   ├── database.py           # 引擎 / 会话 / Base
│   ├── models.py             # SQLAlchemy 模型
│   ├── schemas.py            # Pydantic 模型
│   ├── crud.py               # 数据访问层
│   ├── seed.py               # Demo 数据自动播种
│   ├── demo.py               # 真实感数据生成器
│   ├── stats.py              # 纯统计工具（可单测）
│   ├── services.py           # 服务编排层
│   ├── visualization.py      # Plotly 图表构建器
│   ├── analysis/             # 统计分析方法
│   │   ├── correlation.py    # 相关性
│   │   ├── timeseries.py     # 时间序列 / 移动平均
│   │   ├── anomaly.py        # 异常检测
│   │   ├── clustering.py     # 聚类
│   │   ├── efficiency.py     # 效率模型
│   │   └── whatif.py         # 反事实模拟
│   └── routers/              # API + 页面路由
│       ├── records.py
│       ├── dashboard.py
│       ├── analysis.py
│       └── io.py
├── templates/                # Jinja2 模板
├── static/                   # CSS / JS / plotly.js（离线内置）
├── tests/                    # pytest 测试套件
├── scripts/                  # Demo 数据生成、截图脚本
├── data/                     # SQLite 数据库（本机，不提交）
├── docs/                     # 统计方法说明
├── screenshots/              # 界面截图
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## 统计方法说明

LifeTrace 的每个分析模块都建立在明确的统计方法之上，详见 [docs/statistics.md](docs/statistics.md)。要点：

- **相关系数**：Pearson r，附显著性 p 值。
- **移动平均**：7 日窗口均值，平滑逐日波动。
- **异常检测**：Isolation Forest + 单指标 z-score（较过去 30 天基线）。
- **聚类**：K-Means，k 由轮廓系数自动选择。
- **效率模型**：多元线性回归，报告 R² 与 MAE。

> ⚠️ **相关不代表因果。** 所有结果均为描述性 / 相关性分析，不构成心理或医学诊断。

---

## 隐私说明

- ✅ 所有数据默认保存在**本机** `data/lifetrace.db`（SQLite）。
- ✅ **不需要账号**，不连接任何云端数据库。
- ✅ **不上传**任何个人生活数据。
- ✅ 数据完全由你掌控，可随时导出（CSV / JSON）或删除本地数据库文件。

---

## 测试

```bash
pip install pytest httpx
pytest
```

测试覆盖：数据库、数据录入、统计计算、异常检测、API 端点、核心函数单元测试。

---

## 未来规划

- [ ] 移动端 PWA 支持
- [ ] 目标设定与提醒
- [ ] 多用户档案
- [ ] 更多统计模型（季节性分解、贝叶斯变化点检测）
- [ ] Docker 一键部署

---

## License

[MIT](LICENSE)
