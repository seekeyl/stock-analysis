-- 股票分析项目数据库建表语句
-- 创建数据库
CREATE DATABASE IF NOT EXISTS stock DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
USE stock;

-- 1. 股票列表
CREATE TABLE IF NOT EXISTS stock_list (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL COMMENT '股票代码',
    name VARCHAR(100) COMMENT '股票名称',
    company VARCHAR(255) COMMENT '公司名称',
    list_date DATE COMMENT '上市日期',
    market VARCHAR(10) COMMENT '市场 SH/SZ',
    total_share VARCHAR(50) COMMENT '总股本',
    float_share VARCHAR(50) COMMENT '流通股本',
    industry VARCHAR(100) COMMENT '所属行业',
    UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 历史K线数据
CREATE TABLE IF NOT EXISTS stock_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10,2) COMMENT '开盘价',
    high DECIMAL(10,2) COMMENT '最高价',
    low DECIMAL(10,2) COMMENT '最低价',
    close DECIMAL(10,2) COMMENT '收盘价',
    volume BIGINT COMMENT '成交量(手)',
    amount BIGINT COMMENT '成交额(元)',
    pct_chg DECIMAL(10,4) COMMENT '涨跌幅(%)',
    change_price DECIMAL(10,4) COMMENT '涨跌额',
    turnover_rate DECIMAL(10,4) COMMENT '换手率(%)',
    UNIQUE KEY uk_code_date (code, trade_date),
    INDEX idx_code (code),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 股票新闻
CREATE TABLE IF NOT EXISTS stock_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL COMMENT '股票代码',
    title VARCHAR(500) COMMENT '新闻标题',
    content TEXT COMMENT '新闻内容',
    pub_date DATETIME COMMENT '发布时间',
    source VARCHAR(100) COMMENT '来源',
    url VARCHAR(500) COMMENT '原文链接',
    keywords VARCHAR(200) COMMENT '关键词',
    INDEX idx_code (code),
    INDEX idx_pub_date (pub_date),
    UNIQUE KEY uk_url (url)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 大盘指数
CREATE TABLE IF NOT EXISTS stock_market (
    id INT AUTO_INCREMENT PRIMARY KEY,
    market VARCHAR(10) NOT NULL COMMENT '市场 SH-上证 SZ-深证',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10,2) COMMENT '开盘价',
    high DECIMAL(10,2) COMMENT '最高价',
    low DECIMAL(10,2) COMMENT '最低价',
    close DECIMAL(10,2) COMMENT '收盘价',
    volume BIGINT COMMENT '成交量(手)',
    amount BIGINT COMMENT '成交额(元)',
    pct_chg DECIMAL(10,4) COMMENT '涨跌幅(%)',
    UNIQUE KEY uk_market_date (market, trade_date),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 技术分析结果
CREATE TABLE IF NOT EXISTS stock_daily (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL COMMENT '股票代码',
    name VARCHAR(100) COMMENT '股票名称',
    market VARCHAR(10) COMMENT '市场 SH/SZ',
    latest_price DECIMAL(10,2) COMMENT '最新价',
    change_pct DECIMAL(10,4) COMMENT '涨跌幅(%)',
    turnover_rate DECIMAL(10,4) COMMENT '换手率(%)',
    pe DECIMAL(10,2) COMMENT '市盈率',
    pb DECIMAL(10,2) COMMENT '市净率',
    zscore_10d DECIMAL(10,4) COMMENT 'Z-Score 10日',
    zscore_30d DECIMAL(10,4) COMMENT 'Z-Score 30日',
    zscore_60d DECIMAL(10,4) COMMENT 'Z-Score 60日',
    macd_signal VARCHAR(20) COMMENT 'MACD信号 多头/空头/金叉/死叉',
    macd_dif DECIMAL(10,4) COMMENT 'MACD DIF',
    macd_dea DECIMAL(10,4) COMMENT 'MACD DEA',
    rsi_14 DECIMAL(10,4) COMMENT 'RSI 14日',
    ma_signal VARCHAR(20) COMMENT '均线信号 多头/空头/震荡',
    market_pe DECIMAL(10,2) COMMENT '市场市盈率',
    market_pb DECIMAL(10,2) COMMENT '市场市净率',
    analysis_summary TEXT COMMENT '分析摘要',
    report_json JSON COMMENT '详细报告',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
