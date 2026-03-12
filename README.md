# Stock Analysis Project 📈

股票分析项目 - 基于A股市场数据的技术分析系统

## 项目简介

本项目用于自动分析A股股票的技术指标，生成分析报告，并支持选股策略。

## 目录结构

```
stock/
├── step1_get_stock_list.py    # 获取股票列表
├── step2_analyze.py           # 股票分析主脚本
├── step2_analyze_latest.py    # 最新版分析脚本备份
├── step2_analyze.py.bak       # 旧版备份
├── analyze_sh.py              # 上海股票分析脚本
├── find_doji.py               # 寻找十字星
├── find_doji_v2.py            # 十字星v2版本
├── find_doji_all.py           # 全量十字星查找
├── stock_apis.py              # 股票API封装
├── stock_demo.py              # 示例代码
├── stock_test_all.py          # 全量测试
├── daemon.py                  # 守护进程
├── tmp/                       # 临时文件目录
│   ├── stock_info.csv         # 股票列表数据
│   └── *.md                   # 各股票分析报告
└── README.md                  # 本文件
```

## 环境依赖

```bash
pip install akshare pandas
```

## 快速开始

### 1. 获取股票列表

```bash
python step1_get_stock_list.py
```

### 2. 分析单只股票

```bash
python -c "
import step2_analyze as sa
sa.analyze_one_stock('000001', '平安银行', 'SZ')
"
```

### 3. 批量分析

```bash
# 并行分析上海+深圳
python analyze_sh.py
```

## 功能特性

### 技术指标

- **MACD**: 多头/空头判断，金叉/死叉信号
- **均线系统**: 多头排列，金叉/死叉
- **RSI**: 相对强弱指标
- **Z-Score**: 估值分析（60日/30日/10日）
- **K线形态**: 十字星、锤子线、流星线
- **成交量分析**: 放量交易日识别

### 数据来源

- 数据源: AkShare (东方财富)
- 市场: 上海(SH)、深圳(SZ)、北京(BJ)
- 数据范围: 约4600只股票

## 分析报告示例

每个股票生成一个Markdown报告，包含：

```markdown
# 平安银行 (000001) 分析报告

## 分时段分析
| 指标 | 2年内 | 1年以内 | 本周 |
|------|--------|---------|------|
| 涨跌幅 | -77.67% | -7.68% | 1.20% |

## 估值指标
- MACD: 多头 (DIF:-0.07 DEA:-0.09)
- RSI(14): 58.8 (正常)
- 均线系统: 缠绕

## 资金流向
- 最新价: 10.94
- 净额: 1.17亿
```

## 定时任务

通过OpenClaw设置每日自动分析：

```bash
# 每日19:00运行
openclaw cron create --name "每日股票分析" \
  --schedule "0 19 * * *" \
  --message "请运行 stock 项目的股票分析脚本"
```

## 选股策略

### 技术选股标准

| 指标 | 分数 | 说明 |
|------|------|------|
| MACD多头 | +5 | DIF>DEA |
| MACD金叉 | +3 | DIF上穿DEA |
| 均线多头排列 | +5 | 5日>10日>20日 |
| 均线金叉 | +3 | 短均线向上突破长均线 |
| Z-Score低估 | +3 | Z-Score < -1 |
| 资金净流入 | +3 | 主力资金净流入 |
| RSI正常 | +2 | 30-70区间 |
| 放量 | +2 | 成交量放大 |

### TOP 20 筛选结果

根据技术分析筛选的最优20只股票：
- 100% MACD多头+金叉
- 100% 均线多头排列+金叉
- 100% 资金净流入

## 性能

- 单只股票分析: ~19秒
- 全量4587只: ~10小时（双进程）
- 优化方向: 并行处理、缓存优化

## 常见问题

### Q: 分析失败怎么办？
A: 某些股票数据接口不稳定会自动跳过，不影响其他股票

### Q: 如何查看分析进度？
A: 查看日志或 `ls tmp/*.md | wc -l`

### Q: 数据在哪？
A: `/home/seekey/dev/workspace/openclaw/stock/tmp/`

## 更新日志

### 2026-03-12
- 新增MACD、RSI、均线系统分析
- 优化数据获取速度
- 添加Z-Score估值分析
- 实现技术指标选股功能

## 作者

小龙虾 🦞

---

*本分析仅供参考，不构成投资建议*
