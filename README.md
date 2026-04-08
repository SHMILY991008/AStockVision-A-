# AStockVision：A股数据爬虫与可视化分析系统

基于 Python 实现的 **沪深京 A 股实时数据爬取 + 专业可视化分析** 完整项目，支持自动数据采集、清洗、去重、Excel 导出、图表生成与数据分析报告输出。

------

## ✨ 项目亮点

- 🚀 **实时爬取**：东方财富网 A 股全量行情数据
- 🛡 **稳定反爬**：随机 UA + 请求延时 + 自动重试
- 📊 **专业可视化**：6 合 1 数据仪表盘 + 统计报告
- 📁 **自动导出**：Excel 数据文件 + 高清图表 + MD 分析报告
- ⚡ **轻量化运行**：配置解耦，日志完整，异常安全

------

## 🧰 技术栈

- **爬虫**：requests, fake-useragent, tenacity, tqdm
- **数据处理**：pandas, openpyxl
- **可视化**：matplotlib
- **工具**：logging, json, re, datetime

------

## 📦 快速使用

### 1. 安装依赖

bash

```
pip install -r requirements.txt
```



### 2. 运行程序

bash

```
python main.py
```

### 3. 输出文件

- Excel 数据：`沪深京A股_时间戳.xlsx`
- 可视化图表：`stock_visualizations/`
- 分析报告：`stock_analysis_时间戳_报告.md`
- 运行日志：`spider.log`

------

## 📊 可视化内容

- 涨跌幅分布直方图

- 换手率 TOP20 柱状图

- 最新价 vs 涨跌幅散点图

- 市盈率分布箱线图

- 市净率 vs 市盈率散点图

- 涨跌停分布饼图

  ![](G:\python学习\stockholm-master\stockholm-master\AStockSpider\stock_visualizations\stock_analysis_20260407_213619_dashboard.png)

------

## 📁 项目结构

```
StockVision/
├── A_Stock_Spider.py                # 主程序
├── README.md              # 项目说明
├── requirements.txt       # 依赖清单
├── spider.log             # 日志文件
├── 沪深京A股_xxx.xlsx     # 股票数据
└── stock_visualizations/  # 可视化结果
```

------

## 📌 可配置项（Config 类）

- 爬取页码、每页数量
- 请求延迟、超时时间
- 可视化风格、清晰度、保存路径
- 日志等级、文件前缀

------

## 📝 使用说明

- 支持 **Ctrl + C** 手动中断，自动保存已爬取数据
- 可视化自动适配中文显示
- 数据自动去重，保证唯一性
- 全程日志记录，便于调试与展示