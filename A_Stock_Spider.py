# 导包
import requests
import time
import random
import json
import re
import logging
from datetime import datetime
from fake_useragent import UserAgent
from openpyxl import Workbook
import pandas as pd
from requests import RequestException
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')


# ===================== 配置项解耦 =====================
class Config:
    # 分页配置
    PAGE_START = 1
    PAGE_END = 20
    PAGE_SIZE = 20
    # 请求配置
    REQUEST_DELAY = (0.8, 1.5)
    RETRY_MAX_ATTEMPT = 3  # 最大重试次数
    REQUEST_TIMEOUT = 10  # 请求超时时间
    # URL模板
    URL_TEMPLATE = (
        'https://push2.eastmoney.com/api/qt/clist/get?np=1&fltt=1&invt=2&cb=jQuery37105460204350036134_1766485651718'
        '&fs=m%3A0%2Bt%3A6%2Bf%3A!2%2Cm%3A0%2Bt%3A80%2Bf%3A!2%2Cm%3A1%2Bt%3A2%2Bf%3A!2%2Cm%3A1%2Bt%3A23%2Bf%3A!2%2Cm%3A0%2Bt%3A81%2Bs%3A262144%2Bf%3A!2'
        '&fields=f12%2Cf13%2Cf14%2Cf1%2Cf2%2Cf4%2Cf3%2Cf152%2Cf5%2Cf6%2Cf7%2Cf15%2Cf18%2Cf16%2Cf17%2Cf10%2Cf8%2Cf9%2Cf23'
        '&fid=f3&pn={}&pz={}&po=1&dect=1&ut=fa5fd1943c7b386f172d6893dbfba10b'
        '&wbp2u=3349087659401996%7C0%7C1%7C0%7Cweb&_=1766485652135'
    )
    # 文件配置
    EXCEL_FILE_PREFIX = '沪深京A股'
    # 股票字段映射（增强可读性）
    STOCK_FIELDS_MAP = {
        'f12': '股票代码', 'f14': '股票名称', 'f2': '最新价', 'f3': '涨跌幅',
        'f4': '涨跌额', 'f5': '成交量(手)', 'f6': '成交额', 'f7': '振幅',
        'f15': '最高', 'f16': '最低', 'f17': '今开', 'f18': '昨收',
        'f10': '量比', 'f8': '换手率', 'f9': '市盈率(动态)', 'f23': '市净率'
    }
    # 日志配置
    LOG_FILE = 'spider.log'
    LOG_LEVEL = logging.INFO
    # 可视化配置
    PLOT_STYLE = 'ggplot'  # 绘图风格
    PLOT_DPI = 300  # 图片清晰度
    PLOT_FIGSIZE = (16, 12)  # 图表尺寸
    PLOT_SAVE_PATH = 'stock_visualizations/'  # 可视化结果保存路径
    PLOT_FONT = 'SimHei'  # 中文显示字体（Windows：SimHei，Mac：Arial Unicode MS，Linux：WenQuanYi Micro Hei）


# ===================== 日志初始化 =====================
def init_logger():
    """初始化日志系统"""
    logger = logging.getLogger('EastMoneySpider')
    logger.setLevel(Config.LOG_LEVEL)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 格式配置
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 文件处理器
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


# 初始化全局日志
logger = init_logger()


# ===================== 可视化类 =====================
class StockVisualizer:
    def __init__(self, df):
        self.df = df.copy()
        self._init_plot_style()
        import os
        os.makedirs(Config.PLOT_SAVE_PATH, exist_ok=True)
        self.plot_prefix = f"{Config.PLOT_SAVE_PATH}stock_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._preprocess_data()

    def _preprocess_data(self):
        numeric_fields = ['最新价', '涨跌幅', '涨跌额', '成交量(手)', '成交额', '振幅',
                          '最高', '最低', '今开', '昨收', '量比', '换手率', '市盈率(动态)', '市净率']
        for field in numeric_fields:
            self.df[field] = pd.to_numeric(self.df[field], errors='coerce')

    def _init_plot_style(self):
        plt.rcParams['font.sans-serif'] = [Config.PLOT_FONT]
        plt.rcParams['axes.unicode_minus'] = False
        plt.style.use(Config.PLOT_STYLE)

    def plot_overview_dashboard(self):
        try:
            fig, axes = plt.subplots(2, 3, figsize=Config.PLOT_FIGSIZE)
            fig.suptitle('沪深京A股数据概览', fontsize=20, fontweight='bold', y=0.98)

            axes[0,0].hist(self.df['涨跌幅'].dropna(), bins=50, color='#1f77b4', alpha=0.7, edgecolor='black')
            axes[0,0].axvline(0, color='red', linestyle='--', linewidth=2, label='平盘线')
            axes[0,0].set_title('涨跌幅分布', fontsize=14)
            axes[0,0].legend()
            axes[0,0].grid(alpha=0.3)

            top20 = self.df.nlargest(20, '换手率')[['股票名称', '换手率']].dropna()
            axes[0,1].barh(top20['股票名称'][::-1], top20['换手率'][::-1], color='#ff7f0e')
            axes[0,1].set_title('换手率 TOP20', fontsize=14)
            axes[0,1].grid(alpha=0.3, axis='x')

            valid = self.df[['最新价', '涨跌幅']].dropna()
            scatter = axes[0,2].scatter(valid['最新价'], valid['涨跌幅'], c=valid['涨跌幅'], cmap='RdYlGn', alpha=0.6, s=12)
            axes[0,2].set_title('最新价 vs 涨跌幅', fontsize=14)
            plt.colorbar(scatter, ax=axes[0,2])

            pe_valid = self.df['市盈率(动态)'].dropna()
            if len(pe_valid) > 0:
                axes[1,0].boxplot(pe_valid, patch_artist=True, boxprops=dict(facecolor='#2ca02c', alpha=0.7))
            axes[1,0].set_title('市盈率分布', fontsize=14)

            pb_pe = self.df[['市净率', '市盈率(动态)']].dropna()
            axes[1,1].scatter(pb_pe['市净率'], pb_pe['市盈率(动态)'], color='#d62728', alpha=0.6, s=12)
            axes[1,1].set_title('市净率 vs 市盈率', fontsize=14)

            up = len(self.df[self.df['涨跌幅'] >= 9.5])
            down = len(self.df[self.df['涨跌幅'] <= -9.5])
            normal = len(self.df) - up - down
            axes[1, 2].pie([up, down, normal], labels=['涨停', '跌停', '正常'], autopct='%1.1f%%',
                           colors=['#ff4500', '#1e90ff', '#90ee90'])
            axes[1, 2].set_title('涨跌停分布', fontsize=14)

            plt.tight_layout()
            plt.savefig(f'{self.plot_prefix}_dashboard.png', dpi=Config.PLOT_DPI, bbox_inches='tight')
            plt.close()
            logger.info("✅ 概览图表已保存")
        except Exception as e:
            logger.error(f"绘图失败：{str(e)}")

    def generate_data_report(self):
        try:
            report = f"""
# 沪深京 A 股数据分析报告
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总股票数：{len(self.df)} 只

上涨：{len(self.df[self.df['涨跌幅'] > 0])} 只
下跌：{len(self.df[self.df['涨跌幅'] < 0])} 只
平盘：{len(self.df[self.df['涨跌幅'] == 0])} 只

平均涨跌幅：{self.df['涨跌幅'].mean():.2f}
平均换手率：{self.df['换手率'].mean():.2f}
"""
            with open(f'{self.plot_prefix}_报告.md', 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info("✅ 统计报告已生成")
            print(report)
        except:
            pass

# ===================== 爬虫 =====================
class EastMoneySpider:
    def __init__(self):
        self.headers = {'User-Agent': UserAgent().random}
        self.stock_info_list = []
        self.excel_file_name = f"{Config.EXCEL_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        self.df = None

    @retry(stop=stop_after_attempt(Config.RETRY_MAX_ATTEMPT), wait=wait_random_exponential(multiplier=1, max=10), retry=retry_if_exception_type((RequestException, TimeoutError)), reraise=True)
    def _request_single_url(self, url):
        response = requests.get(url, headers=self.headers, timeout=Config.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text

    def get_stock_data(self, urls):
        success_count = 0
        for url in tqdm(urls, desc="爬取中"):
            time.sleep(random.uniform(*Config.REQUEST_DELAY))
            try:
                content = self._request_single_url(url)
                success_count += 1
                self._parse_single_page(content)
            except Exception as e:
                logger.error(f"请求失败：{e}")
        return success_count

    def _parse_single_page(self, content):
        try:
            json_match = re.search(r'jQuery\d+_\d+\((.*?)\);', content)
            if not json_match: return
            data = json.loads(json_match.group(1))
            if data.get('rc') != 0 or not data.get('data'): return
            stock_list = data['data'].get('diff', [])
            for stock in stock_list:
                info = [stock.get(k, '-') for k in Config.STOCK_FIELDS_MAP.keys()]
                self.stock_info_list.append(info)
        except:
            pass

    def save_to_excel(self):
        if not self.stock_info_list: return
        self.df = pd.DataFrame(self.stock_info_list, columns=list(Config.STOCK_FIELDS_MAP.values()))
        self.df = self.df.drop_duplicates(subset=['股票代码'])
        self.df.to_excel(self.excel_file_name, index=False)
        logger.info(f"✅ Excel已保存：{self.excel_file_name}")

    def run_visualization(self):
        if self.df is None or self.df.empty:
            logger.warning("无数据可绘图")
            return
        viz = StockVisualizer(self.df)
        viz.plot_overview_dashboard()
        viz.generate_data_report()

    def start(self):
        try:
            urls = [Config.URL_TEMPLATE.format(p, Config.PAGE_SIZE) for p in range(Config.PAGE_START, Config.PAGE_END)]
            logger.info(f"开始爬取 {len(urls)} 页")
            cnt = self.get_stock_data(urls)
            if cnt > 0:
                self.save_to_excel()
                self.run_visualization()
                logger.info("🎉 全部完成！")
        except KeyboardInterrupt:
            logger.warning("手动中断")
            if self.stock_info_list:
                self.save_to_excel()
                self.run_visualization()
        except Exception as e:
            logger.error(f"程序执行异常：{str(e)}")

# ===================== 执行入口 =====================
if __name__ == '__main__':
    # 实例化爬虫并运行
    spider = EastMoneySpider()
    spider.start()