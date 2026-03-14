# 股票分析项目 📈

基于A股市场数据的自动化分析系统

## 目录结构

```
stock/
├── .env                 # 数据库配置 (敏感信息，不提交git)
├── .gitignore          # git忽略配置
├── load_env.py         # 加载配置脚本
├── init_db.py          # 数据库初始化
├── daily_update.py     # 每日数据更新 (19:30)
├── analyze_to_db.py   # 技术分析 (23:00)
├── select_stocks.py    # 选股推荐 (08:45)
├── schema.sql          # 建表语句
├── README.md           # 说明文档
└── tmp/               # 临时文件 (不提交git)
    └── recommendation.md
```

## 快速开始

### 1. 配置环境

```bash
cd /home/seekey/dev/workspace/openclaw/stock

# 创建 .env 文件
cat > .env << 'EOF'
DB_HOST=数据库地址
DB_PORT=端口
DB_USER=用户名
DB_PASSWORD=密码
DB_NAME=数据库名
EOF
```

### 2. 初始化数据库

```bash
python init_db.py
```

### 3. 运行定时任务

数据会自动通过 cron 定时任务执行：
- 08:45 - 选股推荐
- 19:30 - 数据更新
- 23:00 - 技术分析

## 数据表

| 表名 | 说明 |
|------|------|
| stock_list | 股票列表 (~4600只) |
| stock_history | 历史K线数据 |
| stock_news | 股票新闻 |
| stock_market | 大盘指数 (上证/深证) |
| stock_daily | 技术分析结果 |

## 脚本说明

### init_db.py
数据库初始化脚本，创建所有表。

```bash
python init_db.py [数据库名]  # 默认 stock
```

### daily_update.py (19:30)
1. 更新股票列表 (stock_list) - 全量
2. 更新30天历史数据 (stock_history) - 全量
3. 更新股票新闻 (stock_news) - 全量
4. 更新大盘信息 (stock_market) - 上证/深证

### analyze_to_db.py (23:00)
从 stock_history 读取数据，计算技术指标：
- Z-Score (10/30/60日)
- MACD (DIF/DEA/信号)
- RSI (14日)
- 均线信号 (多头/空头/震荡)

写入 stock_daily 表。

### select_stocks.py (08:45)
从 stock_daily 筛选优质股票，生成推荐报告。

## 技术指标

| 指标 | 说明 | 选股标准 |
|------|------|---------|
| Z-Score | 估值偏离度 | ≤ -0.5 (低估) |
| MACD | 趋势判断 | 多头/金叉 |
| RSI | 强弱指标 | 30-70 (健康) |
| 均线 | 趋势判断 | 多头排列 |

## 依赖

```bash
pip install akshare pandas pymysql
```

## 注意事项

- `.env` 和 `tmp/` 不会提交到 git
- 首次使用需运行 `init_db.py` 初始化数据库
- 使用 `INSERT IGNORE` 避免重复插入数据

---

**作者**: 小龙虾 🦞

*本分析仅供参考，不构成投资建议*
