import sys
import os
import ctypes
import requests
import urllib3

# 设置 Windows 任务栏 AppUserModelID，确保图标正确显示
try:
    myappid = 'mycompany.myproduct.subproduct.version' # 任意唯一字符串
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import time
import subprocess
import json
from curl_cffi import requests as curlex
from datetime import datetime, time as dtime, timedelta
import winreg
import pyqtgraph as pg
import numpy as np
from PyQt6.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal, QByteArray, QObject, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSystemTrayIcon, QMenu, QFrame, QPushButton, QGridLayout, QButtonGroup, QSizePolicy
from PyQt6.QtGui import QFont, QColor, QAction, QIcon, QPainter, QPixmap, QImage, QCursor, QPainterPath, QPicture, QLinearGradient

# 配置
UPDATE_INTERVAL = 10000  # 10秒刷新一次
# 使用 SGE_AU9999 (国内 AU9999) 和 hf_GC (COMEX黄金)
SINA_API_URL = "http://hq.sinajs.cn/list="
# K线图数据 URL (东方财富)
# klt=5 (5分钟), klt=101 (日线), klt=102 (周线)
# 使用 http 替代 https 以避开部分 TLS 指纹检测
EASTMONEY_KLINE_DOM = "http://push2his.eastmoney.com/api/qt/stock/kline/get?secid=118.AU9999&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt={klt}&fqt=1&end=20500101&lmt={lmt}"
EASTMONEY_KLINE_INTL = "http://push2his.eastmoney.com/api/qt/stock/kline/get?secid=101.GC00Y&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f65&klt={klt}&fqt=1&end=20500101&lmt={lmt}"

# 东方财富实时数据 URL
EASTMONEY_RT_INTL = "http://push2.eastmoney.com/api/qt/stock/get?secid=101.GC00Y&fields=f43,f44,f45,f46,f60,f110,f58,f47,f48,f49,f50,f86"

REFERER_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://finance.sina.com.cn/"
}

EASTMONEY_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive"
}

# SGE 交易时间轴配置 (分钟)
SGE_TIMELINE_MINUTES = 660 # 总交易分钟数 (Night 390 + AM 150 + PM 120)


# 设置 pyqtgraph 全局配置
pg.setConfigOptions(antialias=True, foreground='#AAA', background=None)

def get_sge_timeline():
    """生成 SGE 标准时间轴序列"""
    timeline = []
    # 夜盘: 20:00 - 02:30
    for h in range(20, 24):
        for m in range(60):
            timeline.append(f"{h:02d}:{m:02d}")
    for h in range(0, 2):
        for m in range(60):
            timeline.append(f"{h:02d}:{m:02d}")
    for m in range(31): # 02:00 - 02:30
        timeline.append(f"02:{m:02d}")
        
    # 上午: 09:00 - 11:30
    for h in range(9, 11):
        for m in range(60):
            timeline.append(f"{h:02d}:{m:02d}")
    for m in range(31):
        timeline.append(f"11:{m:02d}")
        
    # 下午: 13:30 - 15:30
    for m in range(30, 60):
        timeline.append(f"13:{m:02d}")
    for h in range(14, 15):
        for m in range(60):
            timeline.append(f"{h:02d}:{m:02d}")
    for m in range(31):
        timeline.append(f"15:{m:02d}")
    return timeline

def get_intl_timeline():
    """生成国际金标准时间轴序列 (07:00 - 06:00)"""
    timeline = []
    # 从 07:00 开始到 23:59
    for h in range(7, 24):
        for m in range(60):
            timeline.append(f"{h:02d}:{m:02d}")
    # 从 00:00 到 06:00
    for h in range(0, 6):
        for m in range(60):
            timeline.append(f"{h:02d}:{m:02d}")
    timeline.append("06:00")
    return timeline

SGE_TIMELINE = get_sge_timeline()
INTL_TIMELINE = get_intl_timeline()

class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data  # list of (time, open, close, low, high)
        self.generatePicture()

    def generatePicture(self):
        # 预先生成图形以提高绘制效率
        self.picture = QPicture()
        p = QPainter(self.picture)
        w = 0.6 # candle width
        for i, (t_str, open_p, close_p, high_p, low_p, *_) in enumerate(self.data):
            if open_p < close_p:
                p.setPen(pg.mkPen('#FF5252', width=1))
                p.setBrush(pg.mkBrush('#FF5252'))
            else:
                p.setPen(pg.mkPen('#4CAF50', width=1))
                p.setBrush(pg.mkBrush('#4CAF50'))
            
            p.drawLine(pg.QtCore.QPointF(i, low_p), pg.QtCore.QPointF(i, high_p))
            # 确保 drawRect 的高度为正值以避免某些环境下的渲染问题
            rect_y = min(open_p, close_p)
            rect_h = abs(open_p - close_p)
            # 如果开收盘价相等，给一个极小的厚度以便可见
            if rect_h == 0: rect_h = 0.01
            p.drawRect(pg.QtCore.QRectF(i - w/2, rect_y, w, rect_h))
        p.end()

    def paint(self, p, *args):
        if self.picture:
            p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        if not self.data:
            return pg.QtCore.QRectF(0, 0, 0, 0)
        # 获取价格范围
        lows = [d[4] for d in self.data]
        highs = [d[3] for d in self.data]
        min_p, max_p = min(lows), max(highs)
        return pg.QtCore.QRectF(-1, min_p, len(self.data) + 1, max_p - min_p)

class InteractiveKLine(pg.PlotWidget):
    """
    交互式 K 线图
    支持分时图 (Line Chart) 和 日K线 (Candlestick)
    """
    hover_data = pyqtSignal(dict)

    def __init__(self, symbol, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.view_mode = "realtime" # "realtime" or "daily"
        self.setMenuEnabled(False)
        self.setMouseEnabled(x=True, y=False)
        self.hideButtons()
        self.setBackground(None)
        
        # 启用坐标轴
        self.showAxis('left')
        self.showAxis('bottom')
        
        # 坐标轴样式
        axis_pen = pg.mkPen(color='#555', width=1)
        font = QFont('Segoe UI', 8)
        
        ax_left = self.getAxis('left')
        ax_left.setPen(axis_pen)
        ax_left.setTextPen(pg.mkPen(color='#888'))
        ax_left.setTickFont(font)
        
        ax_bottom = self.getAxis('bottom')
        ax_bottom.setPen(axis_pen)
        ax_bottom.setTextPen(pg.mkPen(color='#888'))
        ax_bottom.setTickFont(font)
        
        # 分时图组件
        self.curve = self.plot(pen=pg.mkPen(color='#FFD700', width=1.5))
        self.fill = pg.FillBetweenItem(
            pg.PlotDataItem([0, 0]), 
            pg.PlotDataItem([0, 0]), 
            brush=pg.mkBrush(color=(255, 215, 0, 15))
        )
        self.addItem(self.fill)
        
        # K线图组件
        self.candlesticks = None
        self.ma_plots = {} # 存储均线对象
        
        # 添加图例
        self.legend = self.addLegend(offset=(10, 10), labelTextColor='#AAA')
        
        # 十字光标
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color='#888', width=0.8, style=Qt.PenStyle.DashLine))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color='#888', width=0.8, style=Qt.PenStyle.DashLine))
        
        # 昨收/结算辅助线
        self.baseLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color='#555', width=1, style=Qt.PenStyle.DashLine))
        self.baseLabel = pg.TextItem("", color='#888', anchor=(1, 0)) # anchor (1,0) 将文字置于线下方
        
        self.addItem(self.vLine, ignoreBounds=True)
        self.addItem(self.hLine, ignoreBounds=True)
        self.addItem(self.baseLine, ignoreBounds=True)
        self.addItem(self.baseLabel, ignoreBounds=True)
        
        self.vLine.hide()
        self.hLine.hide()
        self.baseLine.hide()
        self.baseLabel.hide()
        
        # 移除原有的 label 提示，改为发射信号给大窗显示
        self.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.data_raw = [] # 原始数据 [(time, open, close, high, low), ...]
        self.data_y = []   # 绘图使用的 y 轴数据 (收盘价)
        self.data_x = []
        self.prev_close = None
        self.current_timeline = [] # 当前模式下的时间轴
        self.full_raw_data = []    # 对应时间轴的完整原始数据 (包含 None)

    def set_view_mode(self, mode):
        self.view_mode = mode
        if mode == "realtime":
            self.curve.show()
            self.fill.show()
            if self.candlesticks: self.candlesticks.hide()
            # 设置底轴为时间格式 (简单处理)
            self.getAxis('bottom').setLabel('时间')
        else:
            self.curve.hide()
            self.fill.hide()
            if self.candlesticks: self.candlesticks.show()
            self.getAxis('bottom').setLabel('日期')

    def update_data(self, kline_data, prev_close=None):
        """
        kline_data: list of (time, open, close, high, low)
        """
        if not kline_data:
            return

        RED = '#FF5252'
        GREEN = '#4CAF50'

        self.prev_close = prev_close
        self.clear()
        self.legend.clear()
        self.addItem(self.vLine, ignoreBounds=True)
        self.addItem(self.hLine, ignoreBounds=True)
        self.addItem(self.baseLine, ignoreBounds=True)
        self.addItem(self.baseLabel, ignoreBounds=True)
        
        self.vLine.hide()
        self.hLine.hide()
        self.baseLine.hide()
        self.baseLabel.hide()

        if self.view_mode == "realtime":
            if "SGE" in self.symbol:
                self.current_timeline = SGE_TIMELINE
                # 寻找 02:30 和 09:00 的位置
                idx_0230 = SGE_TIMELINE.index("02:30")
                idx_0900 = SGE_TIMELINE.index("09:00")
                xticks = [
                    (0, "20:00"),
                    ((idx_0230 + idx_0900) // 2, "02:30/09:00"), # 仅合并夜盘和早盘
                    (len(SGE_TIMELINE) - 1, "15:30"),
                ]
            else:
                self.current_timeline = INTL_TIMELINE
                xticks = [
                    (0, "07:00"),
                    (INTL_TIMELINE.index("14:00"), "14:00"),
                    (INTL_TIMELINE.index("22:00"), "22:00"),
                    (len(INTL_TIMELINE) - 1, "06:00"),
                ]

            total_len = len(self.current_timeline)
            self.data_x = np.arange(total_len)
            full_y = np.full(total_len, np.nan)
            full_raw = [None] * total_len

            # 1. 确定最新数据点及其对应的交易时段起始时间
            last_item = kline_data[-1]
            last_ts = last_item[0]
            l_date_str, l_time_str = last_ts.split(' ') if ' ' in last_ts else (last_ts[:10], last_ts[10:])
            l_dt = datetime.strptime(l_date_str, "%Y-%m-%d")
            l_h = int(l_time_str[:2])
            
            if "SGE" in self.symbol:
                # SGE: 20:00 (前一交易日) - 15:30 (当前交易日)
                if l_h >= 20:
                    session_start_dt = l_dt.replace(hour=20, minute=0)
                else:
                    # 如果当前是凌晨或白天，起始点是前一个自然日(如果是周一则需前移3天)的20:00
                    days = 3 if l_dt.weekday() == 0 else 1
                    session_start_dt = (l_dt - timedelta(days=days)).replace(hour=20, minute=0)
            else:
                # 国际金: 07:00 (当日) - 06:00 (次日)
                if l_h >= 7:
                    session_start_dt = l_dt.replace(hour=7, minute=0)
                else:
                    days = 3 if l_dt.weekday() == 0 else 1
                    session_start_dt = (l_dt - timedelta(days=days)).replace(hour=7, minute=0)

            time_to_idx = {t: i for i, t in enumerate(self.current_timeline)}
            idx_points = []
            
            for d in kline_data:
                t_str = d[0]
                d_date_str, d_time_str = t_str.split(' ') if ' ' in t_str else (t_str[:10], t_str[10:])
                d_dt = datetime.strptime(d_date_str, "%Y-%m-%d").replace(
                    hour=int(d_time_str[:2]), minute=int(d_time_str[3:5])
                )
                
                # 仅保留属于当前交易时段的数据点
                if d_dt < session_start_dt:
                    continue
                
                t_key = d_time_str.strip()[:5]
                idx = time_to_idx.get(t_key)
                if idx is None:
                    continue

                full_y[idx] = d[2]
                full_raw[idx] = d
                idx_points.append((idx, d[2]))

            idx_points.sort(key=lambda x: x[0])
            for (idx_a, val_a), (idx_b, val_b) in zip(idx_points, idx_points[1:]):
                if idx_b <= idx_a + 1:
                    continue
                step_count = idx_b - idx_a + 1
                interp = np.linspace(val_a, val_b, step_count)
                full_y[idx_a:idx_b + 1] = interp

            self.data_y = full_y
            self.full_raw_data = full_raw
            self.data_raw = kline_data

            valid_indices = np.where(~np.isnan(full_y))[0]
            if len(valid_indices) > 0:
                first_idx = int(valid_indices[0])
                last_idx = int(valid_indices[-1])
                # 特殊处理国际金 COMEX (hf_GC): 
                # 即使是分时图，昨收也应使用东方财富实时接口提供的 f60 (结算价)，而不是 K 线第一个点的开盘价。
                # self.symbol == "hf_GC" 时，prev_close 已在 update_ui_with_data 中被设为结算价
                base_price = prev_close if prev_close is not None else float(full_y[first_idx])
                
                # 更新辅助线
                self.baseLine.setPos(base_price)
                self.baseLine.show()
                label_text = "昨收线" if self.symbol == "hf_GC" else "昨收线"
                self.baseLabel.setText(f"{label_text}: {base_price:.2f}")
                # 将文字放在右侧边缘稍往左一点，避免被坐标轴遮挡
                self.baseLabel.setPos(total_len * 0.99, base_price)
                self.baseLabel.show()

                last_val = float(full_y[last_idx])
                color = RED if last_val >= base_price else GREEN

                self.curve = self.plot(
                    self.data_x,
                    self.data_y,
                    pen=pg.mkPen(color=color, width=1.5),
                    connect='finite',
                )

                avg_y = np.full(total_len, np.nan)
                running_sum = 0.0
                running_count = 0
                for i in range(first_idx, last_idx + 1):
                    y = full_y[i]
                    if np.isnan(y):
                        continue
                    running_sum += float(y)
                    running_count += 1
                    avg_y[i] = running_sum / running_count

                self.plot(
                    self.data_x,
                    avg_y,
                    pen=pg.mkPen(color='#2196F3', width=1),
                    connect='finite'
                )
                self.legend.hide() # 隐藏图例

                min_p = float(np.nanmin(full_y))
                max_p = float(np.nanmax(full_y))
                rng = max_p - min_p if max_p != min_p else 1
                base = min_p - rng * 0.1

                fill_x = self.data_x[first_idx:last_idx + 1]
                fill_y = full_y[first_idx:last_idx + 1]
                self.fill = pg.FillBetweenItem(
                    pg.PlotDataItem(fill_x, fill_y),
                    pg.PlotDataItem(fill_x, np.full_like(fill_x, base)),
                    brush=pg.mkBrush(color=(QColor(color).red(), QColor(color).green(), QColor(color).blue(), 25)),
                )
                self.addItem(self.fill)

                y_min = min(float(np.nanmin(full_y)), float(np.nanmin(avg_y)))
                y_max = max(float(np.nanmax(full_y)), float(np.nanmax(avg_y)))
                if prev_close:
                    y_min = min(y_min, prev_close)
                    y_max = max(y_max, prev_close)
                padding = (y_max - y_min) * 0.1
                self.setYRange(y_min - padding, y_max + padding)

            if prev_close:
                ref_line = pg.InfiniteLine(
                    pos=prev_close,
                    angle=0,
                    pen=pg.mkPen(color='#FF9800', width=0.8, style=Qt.PenStyle.DashLine),
                )
                self.addItem(ref_line)

            self.getAxis('bottom').setTicks([xticks])
            self.setXRange(0, total_len - 1, padding=0.02)
            self.legend.hide() # 确保隐藏图例
        else:
            latest_date_str = kline_data[-1][0].split(' ')[0]
            latest_dt = datetime.strptime(latest_date_str, "%Y-%m-%d")

            year = latest_dt.year
            month = latest_dt.month - 3
            if month <= 0:
                month += 12
                year -= 1
            cutoff_dt = datetime(year, month, 1)

            new_data = []
            for d in kline_data:
                try:
                    d_dt = datetime.strptime(d[0].split(' ')[0], "%Y-%m-%d")
                    if d_dt >= cutoff_dt:
                        new_data.append(d)
                except:
                    continue
            kline_data = new_data

            self.data_raw = kline_data
            self.data_y = np.array([d[2] for d in kline_data])
            # 对于日 K 线图，如果有外部传入的昨收（结算价），可以用于计算涨跌逻辑，但 K 线绘图本身基于成交数据。
            # 这里保持 K 线绘图数据不变。
            self.data_x = np.arange(len(self.data_y))

            def moving_average(data, n):
                ret = np.cumsum(data, dtype=float)
                ret[n:] = ret[n:] - ret[:-n]
                return ret[n - 1:] / n

            if len(self.data_y) >= 5:
                ma5 = moving_average(self.data_y, 5)
                self.plot(np.arange(4, len(self.data_y)), ma5, pen=pg.mkPen(color='#00E5FF', width=1.2), name="MA5 (5日均线)")
            if len(self.data_y) >= 10:
                ma10 = moving_average(self.data_y, 10)
                self.plot(np.arange(9, len(self.data_y)), ma10, pen=pg.mkPen(color='#FFD700', width=1.2), name="MA10 (10日均线)")
            if len(self.data_y) >= 20:
                ma20 = moving_average(self.data_y, 20)
                self.plot(np.arange(19, len(self.data_y)), ma20, pen=pg.mkPen(color='#FF4081', width=1.2), name="MA20 (20日均线)")

            self.legend.show()

            self.candlesticks = CandlestickItem(self.data_raw)
            self.addItem(self.candlesticks)

            l = len(self.data_raw)
            xticks = []
            last_month = None
            for i in range(l):
                date_str = self.data_raw[i][0].split(' ')[0]
                month_str = date_str[:7]
                if month_str != last_month:
                    xticks.append((i, month_str))
                    last_month = month_str

            if len(xticks) > 5:
                xticks = xticks[-5:]

            self.getAxis('bottom').setTicks([xticks])

            if l > 0:
                display_range = 80 if l > 80 else l
                self.setXRange(l - display_range, l)

        self.autoRange(padding=0.05)

    def on_mouse_moved(self, evt):
        if not len(self.data_y):
            return
        
        pos = evt
        if self.sceneBoundingRect().contains(pos):
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            index = int(mousePoint.x() + 0.5)
            if not (0 <= index < len(self.data_y)):
                self.hide_cursor()
                return

            if self.view_mode == "realtime":
                idx = index
                if np.isnan(self.data_y[idx]):
                    left = idx - 1
                    right = idx + 1
                    best = None
                    while left >= 0 or right < len(self.data_y):
                        if left >= 0 and not np.isnan(self.data_y[left]):
                            best = left
                            break
                        if right < len(self.data_y) and not np.isnan(self.data_y[right]):
                            best = right
                            break
                        left -= 1
                        right += 1

                    if best is None:
                        self.hide_cursor()
                        return
                    idx = best

                price = float(self.data_y[idx])
                self.vLine.setPos(idx)
                self.hLine.setPos(price)
                self.vLine.show()
                self.hLine.show()

                finite = np.where(~np.isnan(self.data_y))[0]
                if len(finite) == 0:
                    self.hide_cursor()
                    return

                base = self.prev_close if self.prev_close else float(self.data_y[int(finite[0])])
                diff = price - base
                percent = (diff / base * 100) if base else 0
                
                # 获取日期
                raw_item = self.full_raw_data[idx] if idx < len(self.full_raw_data) else None
                date_str = ""
                if raw_item:
                    date_str = raw_item[0].split(' ')[0] if ' ' in raw_item[0] else raw_item[0][:10]
                elif len(self.data_raw) > 0:
                    # 备选：使用最后一条数据的日期
                    date_str = self.data_raw[-1][0].split(' ')[0] if ' ' in self.data_raw[-1][0] else self.data_raw[-1][0][:10]
                
                time_val = self.current_timeline[idx] if idx < len(self.current_timeline) else ""
                full_time = f"{date_str} {time_val}".strip()

                info = {
                    "mode": "realtime",
                    "time": full_time,
                    "price": price,
                    "diff": diff,
                    "percent": percent
                }
            else:
                raw_item = self.data_raw[index]
                price = raw_item[2]
                self.vLine.setPos(index)
                self.hLine.setPos(price)
                self.vLine.show()
                self.hLine.show()

                prev_c = self.data_y[index - 1] if index > 0 else raw_item[1]
                diff = raw_item[2] - prev_c
                percent = (diff / prev_c * 100) if prev_c else 0

                info = {
                    "mode": "daily",
                    "time": raw_item[0],
                    "open": raw_item[1],
                    "close": raw_item[2],
                    "high": raw_item[3],
                    "low": raw_item[4],
                    "vol": raw_item[5],
                    "diff": diff,
                    "percent": percent,
                    "prev_close": prev_c
                }

            self.hover_data.emit(info)
        else:
            self.hide_cursor()

    def hide_cursor(self):
        self.vLine.hide()
        self.hLine.hide()
        self.hover_data.emit({}) # 发送空数据表示隐藏

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.hide_cursor()
def is_market_open():
    """
    判断当前是否在交易时间内
    国内黄金 (SGE): 09:00-11:30, 13:30-15:30, 20:00-02:30 (次日)
    国际黄金: 周一 06:00 至 周六 06:00 几乎 24 小时 (北京时间)
    """
    now = datetime.now()
    weekday = now.weekday() # 0-4 为周一至周五，5-6 为周六日
    curr_time = now.time()

    # 1. 国际市场检测 (周六 06:00 至 周一 06:00 休市)
    is_intl_open = True
    if weekday == 5: # 周六
        if curr_time > dtime(6, 0):
            is_intl_open = False
    elif weekday == 6: # 周日
        is_intl_open = False
    elif weekday == 0: # 周一
        if curr_time < dtime(6, 0):
            is_intl_open = False
    
    # 2. 国内市场检测 (SGE)
    is_domestic_open = False
    is_domestic_pause = False
    # 周一至周五的白天和周一至周五的晚上 (20:00-00:00)
    if weekday < 5:
        # 白天
        if (dtime(9, 0) <= curr_time <= dtime(11, 31)) or \
           (dtime(13, 30) <= curr_time <= dtime(15, 31)):
            is_domestic_open = True
        # 盘中休市: 仅包含午休 11:31 - 13:30
        elif (dtime(11, 31) < curr_time < dtime(13, 30)):
            is_domestic_pause = True
            
        # 夜盘开始 (20:00 - 24:00)
        if curr_time >= dtime(20, 0):
            is_domestic_open = True
            
    # 夜盘跨天部分: 周二至周六的 00:00 - 02:30
    if 1 <= weekday <= 5:
        if curr_time <= dtime(2, 30):
            is_domestic_open = True
        # 凌晨休市: 02:30 - 09:00 (仅在周二至周五显示为盘中休市，周六凌晨 02:30 后为收盘)
        elif dtime(2, 30) < curr_time < dtime(9, 0) and weekday < 5:
            is_domestic_pause = True
    
    return is_intl_open or is_domestic_open, is_domestic_open, is_intl_open, is_domestic_pause

class PriceFetcher(QThread):
    price_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._manual_trigger = False
        self._interval = 10 # 默认 10s
        self._paused = False # 新增暂停标志
        # 记录上一次的状态，用于确保休盘后能抓取到最后一次数据
        self._last_dom_open = False
        self._last_intl_open = False
        # 保存最后一次成功获取的数据
        self.last_data = {
            "au9999": {"price": "0.00", "change": "0.00", "percent": "0.00%", "high": "0.00", "low": "0.00", "open": "0.00", "prev": "0.00", "open_status": False},
            "intl": {"price": "0.00", "change": "0.00", "percent": "0.00%", "high": "0.00", "low": "0.00", "open": "0.00", "prev": "0.00", "open_status": False},
            "status": "closed",
            "time": "--:--:--"
        }

    def set_paused(self, paused):
        self._paused = paused

    def set_interval(self, seconds):
        self._interval = seconds

    def run(self):
        while True:
            # 仅在未暂停时执行抓取
            if not self._paused:
                self.fetch()
            self._manual_trigger = False
            
            # 每 100ms 检查一次，直到达到间隔时间或被手动触发
            elapsed = 0
            while elapsed < self._interval and not self._manual_trigger:
                time.sleep(0.1)
                elapsed += 0.1

    def trigger_fetch(self):
        # 仅设置标志，由 run 循环在下一次迭代中处理或立即跳过休眠
        self._manual_trigger = True

    def fetch(self):
        try:
            is_open, dom_open, intl_open, dom_pause = is_market_open()
            
            # 更新状态
            self.last_data["status"] = "open" if is_open else "closed"
            self.last_data["au9999"]["open_status"] = dom_open
            self.last_data["au9999"]["pause_status"] = dom_pause # 新增国内盘中休市状态
            self.last_data["intl"]["open_status"] = intl_open
            
            # 跟踪本次尝试更新是否全部成功
            any_attempted = False
            all_success = True

            # 1. 国内黄金 (SGE) - 只在交易中、手动触发或刚休盘时获取（确保抓到最后一次数据）
            if dom_open or self._manual_trigger or self._last_dom_open:
                any_attempted = True
                try:
                    res = requests.get(f"{SINA_API_URL}SGE_AU9999", headers=REFERER_HEADER, timeout=3)
                    content = res.content.decode('gbk', 'ignore')
                    if 'SGE_AU9999' in content and '"' in content:
                        parts = content.split('"')[1].split(',')
                        if len(parts) > 16:
                            curr = float(parts[3])
                            if curr > 0:
                                open_p = float(parts[6])
                                prev = float(parts[5])
                                high = float(parts[7])
                                low = float(parts[8])
                                data_time = parts[16]
                                diff = curr - prev
                                percent = (diff / prev) * 100 if prev != 0 else 0
                                self.last_data["au9999"].update({
                                    "price": f"{curr:.2f}",
                                    "change": f"{diff:+.2f}",
                                    "percent": f"{percent:+.2f}%",
                                    "high": f"{high:.2f}",
                                    "low": f"{low:.2f}",
                                    "open": f"{open_p:.2f}",
                                    "prev": f"{prev:.2f}",
                                    "data_time": data_time
                                })
                            else: all_success = False
                        else: all_success = False
                    else: all_success = False
                except Exception as e:
                    print(f"Domestic Sina fetch error: {e}")
                    all_success = False

            # 2. 请求东方财富 API (获取 COMEX 黄金数据) - 只在交易中、手动触发或刚休盘时获取
            if intl_open or self._manual_trigger or self._last_intl_open:
                any_attempted = True
                try:
                    res = requests.get(EASTMONEY_RT_INTL, headers=EASTMONEY_HEADER, timeout=5)
                    data = res.json()
                    if data and data.get("data"):
                        d = data["data"]
                        curr = d.get("f43", 0) / 10
                        prev = d.get("f60", 0) / 10
                        open_p = d.get("f46", 0) / 10
                        high = d.get("f44", 0) / 10
                        low = d.get("f45", 0) / 10
                        diff = curr - prev
                        percent = (diff / prev) * 100 if prev != 0 else 0
                        
                        # 解析行情交易时间 (f86 是 Unix 时间戳)
                        ts = d.get("f86")
                        if ts:
                            data_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            data_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                        volume = d.get("f47", 0)
                        self.last_data["intl"].update({
                            "price": f"{curr:.2f}",
                            "change": f"{diff:+.2f}",
                            "percent": f"{percent:+.2f}%",
                            "high": f"{high:.2f}",
                            "low": f"{low:.2f}",
                            "open": f"{open_p:.2f}",
                            "prev": f"{prev:.2f}",
                            "data_time": data_time,
                            "volume": f"{volume/1000:.1f}K" if volume > 0 else "--",
                            "turnover": "--",
                            "hold": "--"
                        })
                    else: all_success = False
                except Exception as e:
                    print(f"International Eastmoney fetch error: {e}")
                    all_success = False
            
            # 更新状态记录
            self._last_dom_open = dom_open
            self._last_intl_open = intl_open
            
            # 仅当所有尝试的请求都成功时，才更新刷新时间
            if any_attempted and all_success:
                self.last_data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.price_updated.emit(self.last_data)

        except Exception as e:
            print(f"General fetch error: {e}")

class DetailWindow(QWidget):
    """
    详情放大页面
    """
    def __init__(self, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        # 分开存储两个市场的模式
        self.view_modes = {
            "hf_GC": "realtime",
            "SGE_AU9999": "realtime"
        }
        self.last_prices = {
            "hf_GC": 0.0,
            "SGE_AU9999": 0.0
        }
        # 记录上一次的状态，确保抓取到最后一次数据
        self._last_dom_open = False
        self._last_intl_open = False
        self.drag_pos = None
        self.init_ui()
        
        # 10秒刷新的定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fetch_detail_data)
        self.timer.start(10000)
        
        # 保存最后一次获取的数据，用于对比是否需要刷新 K 线
        self.last_kline_update = 0

    def init_ui(self):
        self.setWindowTitle("Market Insight")
        if self.parent_widget:
            self.setWindowIcon(self.parent_widget.create_tray_icon())
        self.setFixedSize(1000, 680)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0) # 初始透明，用于入场动画
        
        # 主容器：风格与小框保持一致
        self.container = QFrame(self)
        self.container.setObjectName("detailContainer")
        self.container.setGeometry(10, 10, 980, 660)
        self.container.setStyleSheet("""
            QFrame#detailContainer {
                background-color: rgba(25, 25, 25, 245);
                border: 1px solid rgba(255, 215, 0, 80);
                border-radius: 12px;
            }
        """)
        
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        main_vbox = QVBoxLayout(self.container)
        main_vbox.setContentsMargins(20, 15, 20, 15)
        main_vbox.setSpacing(15)
        
        # 顶部栏
        top_hbox = QHBoxLayout()
        self.refresh_time_label = QLabel("更新于 ----- --:--:--")
        self.refresh_time_label.setStyleSheet("color: rgba(255, 255, 255, 120); font-size: 11px; font-family: 'Segoe UI'; min-width: 150px;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #888; border: none; font-size: 16px; }
            QPushButton:hover { color: #FF5252; background-color: rgba(255, 82, 82, 20); border-radius: 12px; }
        """)
        close_btn.clicked.connect(self.hide_and_resume)
        
        top_hbox.addWidget(self.refresh_time_label)
        top_hbox.addStretch()
        top_hbox.addWidget(close_btn)
        main_vbox.addLayout(top_hbox)
        
        # 内容区域：左右两个行情卡片
        content_hbox = QHBoxLayout()
        content_hbox.setSpacing(20)
        
        self.intl_box = self.create_detail_box("COMEX 黄金 GC", "hf_GC")
        self.dom_box = self.create_detail_box("国内 AU9999", "SGE_AU9999")
        
        content_hbox.addLayout(self.intl_box, 1)
        content_hbox.addLayout(self.dom_box, 1)
        
        main_vbox.addLayout(content_hbox)

    def on_mode_changed(self, btn):
        # 找到按钮所属的市场
        symbol = btn.property("symbol")
        new_mode = "realtime" if btn.text() == "分时" else "daily"
        
        if new_mode != self.view_modes.get(symbol):
            self.view_modes[symbol] = new_mode
            kline_widget = self.findChild(InteractiveKLine, f"{symbol}_kline")
            if kline_widget:
                kline_widget.set_view_mode(new_mode)
            
            # 切换模式后恢复按钮显示并隐藏悬停显示
            hover_lbl = self.findChild(QLabel, f"{symbol}_hover_info")
            btn_container = self.findChild(QWidget, f"{symbol}_tab_container")
            if hover_lbl: hover_lbl.hide()
            if btn_container: btn_container.show()
                
            # 立即刷新该市场的数据
            self.update_single_kline(symbol)

    def on_chart_hover(self, info, symbol):
        """处理 K 线图悬停信号"""
        hover_lbl = self.findChild(QLabel, f"{symbol}_hover_info")
        tab_container = self.findChild(QWidget, f"{symbol}_tab_container")
        if not hover_lbl or not tab_container: return
        
        if not info:
            hover_lbl.hide()
            tab_container.show()
            return
            
        # 隐藏切换按钮，显示悬停数据
        tab_container.hide()
        hover_lbl.show()
        
        # 涨跌配色
        RED = "#FF5252"
        GREEN = "#4CAF50"
        color = RED if info.get("diff", 0) >= 0 else GREEN
        
        # 标签名：COMEX 黄金显示“结算”，其他显示“收”
        close_label = "收" if symbol == "hf_GC" and info["mode"] == "daily" else "收"
        
        if info["mode"] == "realtime":
            # 分时图布局：仅一行，显示时间、价格、涨跌额、涨跌幅
            font_size = "13px"
            value_color = "#FFFFFF" # 纯白色
            
            html = f"""
                <table style='width:100%; table-layout:fixed; border-collapse:collapse;'>
                    <tr>
                        <td width='32%' style='color:{value_color}; font-size:{font_size}; text-align:left;'>{info['time']}</td>
                        <td width='23%' style='color:{color}; font-size:{font_size}; text-align:left;'>价 {info['price']:.2f}</td>
                        <td width='22%' style='color:{color}; font-size:{font_size}; text-align:left;'>额 {info['diff']:+.2f}</td>
                        <td width='23%' style='color:{color}; font-size:{font_size}; text-align:left;'>幅 {info['percent']:+.2f}%</td>
                    </tr>
                </table>
            """
        else:
            # 日K线布局：两行四列，等间隔水平分布
            prev_c = info.get("prev_close", info["open"])
            o_color = RED if info["open"] >= prev_c else GREEN
            h_color = RED if info["high"] >= prev_c else GREEN
            l_color = RED if info["low"] >= prev_c else GREEN
            
            # 成交量转换为万手
            vol_wan = info['vol'] / 10000.0
            
            # 字体大小统一为 13px (与右侧今开等数据一致)
            font_size = "13px"
            
            # 颜色统一：日期和成交标签使用纯白色，与右侧数值颜色一致
            value_color = "#FFFFFF"
            
            html = f"""
                <table style='width:100%; table-layout:fixed; border-collapse:collapse;'>
                    <tr>
                        <td width='30%' style='color:{value_color}; font-size:{font_size}; text-align:left; padding-bottom:10px;'>{info['time']}</td>
                        <td width='23%' style='color:{o_color}; font-size:{font_size}; text-align:left; padding-bottom:10px;'>开 {info['open']:.2f}</td>
                        <td width='23%' style='color:{h_color}; font-size:{font_size}; text-align:left; padding-bottom:10px;'>高 {info['high']:.2f}</td>
                        <td width='24%' style='color:{color}; font-size:{font_size}; text-align:left; padding-bottom:10px;'>幅 {info['percent']:+.2f}%</td>
                    </tr>
                    <tr>
                        <td width='30%' style='color:{value_color}; font-size:{font_size}; text-align:left;'>成交 {vol_wan:.1f}万手</td>
                        <td width='23%' style='color:{color}; font-size:{font_size}; text-align:left;'>{close_label} {info['close']:.2f}</td>
                        <td width='23%' style='color:{l_color}; font-size:{font_size}; text-align:left;'>低 {info['low']:.2f}</td>
                        <td width='24%' style='color:{color}; font-size:{font_size}; text-align:left;'>额 {info['diff']:+.2f}</td>
                    </tr>
                </table>
            """
        
        hover_lbl.setText(html)

    def create_detail_box(self, title, symbol):
        box_vbox = QVBoxLayout()
        box_vbox.setSpacing(10)
        box_vbox.setContentsMargins(0, 0, 0, 0)
        
        # 1. 标题、代码与状态 (紧凑布局)
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(2)
        
        title_hbox = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #FFD700; font-size: 18px; font-weight: bold; font-family: 'Microsoft YaHei';")
        
        title_hbox.addWidget(title_lbl)
        title_hbox.addStretch()
        header_vbox.addLayout(title_hbox)
        
        status_hbox = QHBoxLayout()
        status_text = QLabel("已收盘")
        status_text.setObjectName(f"{symbol}_status_text")
        status_text.setStyleSheet("color: #999; font-size: 12px;")
        
        status_time = QLabel("--")
        status_time.setObjectName(f"{symbol}_status_time")
        status_time.setStyleSheet("color: #999; font-size: 12px; margin-left: 10px;")
        
        status_hbox.addWidget(status_text)
        status_hbox.addWidget(status_time)
        status_hbox.addStretch()
        header_vbox.addLayout(status_hbox)
        box_vbox.addLayout(header_vbox)
        
        # 2. 价格与多列数据网格
        price_grid_hbox = QHBoxLayout()
        price_grid_hbox.setSpacing(20)
        
        # 左侧价格区
        price_vbox = QVBoxLayout()
        price_lbl = QLabel("--")
        price_lbl.setObjectName(f"{symbol}_price")
        price_lbl.setStyleSheet("color: #FF5252; font-size: 42px; font-weight: bold; font-family: 'Segoe UI'; min-width: 180px;")
        
        change_hbox = QHBoxLayout()
        change_val_lbl = QLabel("--")
        change_val_lbl.setObjectName(f"{symbol}_change_val")
        change_val_lbl.setStyleSheet("color: #FF5252; font-size: 16px; font-weight: 500; min-width: 70px;")
        
        change_pct_lbl = QLabel("--")
        change_pct_lbl.setObjectName(f"{symbol}_change_pct")
        change_pct_lbl.setStyleSheet("color: #FF5252; font-size: 16px; font-weight: 500; margin-left: 10px; min-width: 80px;")
        
        change_hbox.addWidget(change_val_lbl)
        change_hbox.addWidget(change_pct_lbl)
        change_hbox.addStretch()
        
        price_vbox.addWidget(price_lbl)
        price_vbox.addLayout(change_hbox)
        price_grid_hbox.addLayout(price_vbox)
        
        # 右侧数据网格 (两列)
        grid = QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(8)
        
        fields = [
            ("今  开", f"{symbol}_open"), ("最高", f"{symbol}_high"), 
            ("昨  收", f"{symbol}_prev"), ("最低", f"{symbol}_low")
        ]
        
        for i, (label, obj_name) in enumerate(fields):
            row, col = i % 2, (i // 2) * 2
            
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #999; font-size: 13px;")
            val = QLabel("--")
            val.setObjectName(obj_name)
            val.setStyleSheet("color: #EEE; font-size: 13px; font-weight: 500; min-width: 75px;")
            
            grid.addWidget(lbl, row, col)
            grid.addWidget(val, row, col + 1)
            
        price_grid_hbox.addStretch()
        price_grid_hbox.addLayout(grid)
        box_vbox.addLayout(price_grid_hbox)
        
        # 3. 切换与悬停数据容器 (使用叠加布局或简单的显示/隐藏切换)
        stack_container = QWidget()
        stack_container.setFixedHeight(65) # 增加高度以适应三行显示
        stack_vbox = QVBoxLayout(stack_container)
        stack_vbox.setContentsMargins(0, 0, 0, 0)
        
        # --- Tab 容器 ---
        tab_container = QWidget()
        tab_container.setObjectName(f"{symbol}_tab_container")
        tab_hbox = QHBoxLayout(tab_container)
        tab_hbox.setContentsMargins(0, 0, 0, 0)
        
        btn_realtime = QPushButton("分时")
        btn_daily = QPushButton("日K")
        
        # 选项卡样式
        tab_style = """
            QPushButton {
                background-color: transparent;
                color: #AAA;
                border: none;
                font-size: 15px;
                font-weight: 500;
                padding: 5px 20px;
                min-width: 80px;
            }
            QPushButton:checked {
                color: #2196F3;
                border-bottom: 2px solid #2196F3;
            }
            QPushButton:hover {
                color: #DDD;
            }
        """
        
        mode_group = QButtonGroup(self)
        for btn in [btn_realtime, btn_daily]:
            btn.setCheckable(True)
            btn.setProperty("symbol", symbol)
            btn.setStyleSheet(tab_style)
            mode_group.addButton(btn)
        
        btn_realtime.setChecked(True)
        mode_group.buttonClicked.connect(self.on_mode_changed)
        
        tab_hbox.addStretch()
        tab_hbox.addWidget(btn_realtime)
        tab_hbox.addSpacing(40)
        tab_hbox.addWidget(btn_daily)
        tab_hbox.addStretch()
        
        # --- 悬停信息 Label ---
        hover_info_lbl = QLabel("")
        hover_info_lbl.setObjectName(f"{symbol}_hover_info")
        hover_info_lbl.setStyleSheet("color: #EEE; font-size: 13px; line-height: 1.2;")
        hover_info_lbl.setFixedHeight(60) # 明确高度
        hover_info_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        hover_info_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hover_info_lbl.hide()
        
        stack_vbox.addWidget(tab_container)
        stack_vbox.addWidget(hover_info_lbl)
        
        box_vbox.addWidget(stack_container)
        
        # 4. K 线图组件
        kline_widget = InteractiveKLine(symbol)
        kline_widget.setObjectName(f"{symbol}_kline")
        kline_widget.setFixedHeight(350)
        # 连接悬停信号
        kline_widget.hover_data.connect(lambda info, s=symbol: self.on_chart_hover(info, s))
        box_vbox.addWidget(kline_widget)
        
        return box_vbox

    def show_and_fetch(self):
        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        target_pos = (screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2
        self.move(target_pos[0], target_pos[1])
        
        # 入场动画：透明度 + 轻微位移
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 通知主窗口暂停小框获取
        if self.parent_widget:
            self.parent_widget.fetcher.set_paused(True)
            self.parent_widget.hide() # 隐藏小框
            
        self.show()
        self.anim.start()
        
        self.fetch_detail_data(force=True) 
        self.update_klines()
        self.timer.start(10000)

    def hide_and_resume(self):
        # 退场动画
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.finished.connect(self._on_hide_finished)
        self.anim.start()

    def _on_hide_finished(self):
        self.timer.stop()
        self.hide()
        
        # 恢复小框获取
        if self.parent_widget:
            self.parent_widget.fetcher.set_paused(False)
            self.parent_widget.show()
            # 切换回小框时，主动触发一次远程获取
            self.parent_widget.fetcher.trigger_fetch()
            # 同样给小框一个渐显效果
            self.parent_widget.setWindowOpacity(0.0)
            self.p_anim = QPropertyAnimation(self.parent_widget, b"windowOpacity")
            self.p_anim.setDuration(300)
            self.p_anim.setStartValue(0.0)
            self.p_anim.setEndValue(1.0)
            self.p_anim.start()

    def fetch_detail_data(self, force=False):
        is_open, dom_open, intl_open, dom_pause = is_market_open()
        
        # 跟踪数据获取是否全部成功
        any_attempted = False
        sge_success = True
        intl_success = True

        # 1. 使用新浪获取 SGE 精准数据 - 交易中、强制获取或刚休盘
        if dom_open or force or self._last_dom_open:
            any_attempted = True
            sge_success = False # 先重置为失败
            try:
                res = requests.get(f"{SINA_API_URL}SGE_AU9999", headers=REFERER_HEADER, timeout=3)
                content = res.content.decode('gbk', 'ignore')
                if 'SGE_AU9999' in content and '"' in content:
                    parts = content.split('"')[1].split(',')
                    if len(parts) > 16:
                        curr = float(parts[3])
                        if curr > 0:
                            open_p = float(parts[6])
                            prev = float(parts[5])
                            high = float(parts[7])
                            low = float(parts[8])
                            data_time = parts[16]
                            self.update_ui_with_data("SGE_AU9999", curr, prev, open_p, high, low, data_time, dom_open, dom_pause)
                            sge_success = True # 标记成功
            except Exception as e:
                print(f"Detail domestic Sina fetch error: {e}")
        else:
            # 休市期间，显示最后一次的状态
            lbl = self.findChild(QLabel, "SGE_AU9999_status_text")
            if lbl: lbl.setText("已收盘" if not dom_pause else "盘中休市")

        # 2. 通过东方财富获取 COMEX 黄金数据 - 交易中、强制获取或刚休盘
        if intl_open or force or self._last_intl_open:
            any_attempted = True
            intl_success = False # 先重置为失败
            try:
                res = requests.get(EASTMONEY_RT_INTL, headers=EASTMONEY_HEADER, timeout=5)
                data = res.json()
                if data and data.get("data"):
                    d = data["data"]
                    curr = d.get("f43", 0) / 10
                    prev = d.get("f60", 0) / 10
                    open_p = d.get("f46", 0) / 10
                    high = d.get("f44", 0) / 10
                    low = d.get("f45", 0) / 10
                    
                    # 解析行情交易时间 (f86 是 Unix 时间戳)
                    ts = d.get("f86")
                    if ts:
                        data_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        data_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 国际金暂不处理盘中休市状态，传 False
                    self.update_ui_with_data("hf_GC", curr, prev, open_p, high, low, data_time, intl_open, False)
                    intl_success = True # 标记成功
            except Exception as e:
                print(f"Detail international Eastmoney fetch error: {e}")
        else:
            # 休市期间，更新状态显示
            lbl = self.findChild(QLabel, "hf_GC_status_text")
            if lbl: lbl.setText("已收盘")

        # 更新状态记录
        self._last_dom_open = dom_open
        self._last_intl_open = intl_open

        # 只有当尝试获取的数据都成功时，才更新顶部的时间戳
        if any_attempted and sge_success and intl_success:
            refresh_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.refresh_time_label.setText(f"更新于 {refresh_time}")

    def update_ui_with_data(self, symbol, curr, prev, open_p, high, low, data_time, open_status, pause_status):
        self.last_prices[symbol] = prev # 存储昨收，供 K 线绘制基准
        diff = curr - prev
        percent = (diff / prev) * 100 if prev != 0 else 0
        
        # 寻找对应的 Label
        price_lbl = self.findChild(QLabel, f"{symbol}_price")
        change_val_lbl = self.findChild(QLabel, f"{symbol}_change_val")
        change_pct_lbl = self.findChild(QLabel, f"{symbol}_change_pct")
        status_text = self.findChild(QLabel, f"{symbol}_status_text")
        status_time = self.findChild(QLabel, f"{symbol}_status_time")
        
        # 网格数据
        open_lbl = self.findChild(QLabel, f"{symbol}_open")
        high_lbl = self.findChild(QLabel, f"{symbol}_high")
        low_lbl = self.findChild(QLabel, f"{symbol}_low")
        prev_lbl = self.findChild(QLabel, f"{symbol}_prev")
        
        RED = "#FF5252"
        GREEN = "#4CAF50"
        ORANGE = "#FF9800"
        color = RED if diff >= 0 else GREEN
        
        if price_lbl:
            price_lbl.setText(f"{curr:.2f}")
            price_lbl.setStyleSheet(f"color: {color}; font-size: 42px; font-weight: bold; font-family: 'Segoe UI';")
        
        if change_val_lbl:
            change_val_lbl.setText(f"{diff:+.2f}")
            change_val_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 500;")
            
        if change_pct_lbl:
            change_pct_lbl.setText(f"{percent:+.2f}%")
            change_pct_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 500; margin-left: 10px;")
        
        if status_text:
            if open_status:
                txt, clr = "交易中", GREEN
            elif pause_status:
                txt, clr = "盘中休市", ORANGE
            else:
                txt, clr = "已收盘", "#999"
            status_text.setText(txt)
            status_text.setStyleSheet(f"color: {clr}; font-size: 12px;")
            
        if status_time:
             # 状态栏显示数据本身的采集时间
             status_time.setText(data_time)
             
         # 为开、高、低添加红绿颜色逻辑 (对比昨收)
        o_color = RED if open_p >= prev else GREEN
        h_color = RED if high >= prev else GREEN
        l_color = RED if low >= prev else GREEN
        
        if open_lbl: 
            open_lbl.setText(f"{open_p:.2f}")
            open_lbl.setStyleSheet("color: #EEE; font-size: 13px; font-weight: 500; min-width: 60px;")
        if high_lbl: 
            high_lbl.setText(f"{high:.2f}")
            high_lbl.setStyleSheet("color: #EEE; font-size: 13px; font-weight: 500; min-width: 60px;")
        if low_lbl: 
            low_lbl.setText(f"{low:.2f}")
            low_lbl.setStyleSheet("color: #EEE; font-size: 13px; font-weight: 500; min-width: 60px;")
        if prev_lbl: 
            prev_lbl.setText(f"{prev:.2f}")
            prev_lbl.setStyleSheet("color: #EEE; font-size: 13px; font-weight: 500; min-width: 60px;")

    def update_klines(self):
        """刷新大窗所有 K 线数据"""
        for symbol in ["hf_GC", "SGE_AU9999"]:
            self.update_single_kline(symbol)

    def update_single_kline(self, symbol):
        """刷新单个市场的 K 线"""
        mode = self.view_modes.get(symbol, "realtime")
        
        if mode == "realtime":
            klt = "1" # 改为 1 分钟 K 线，解决“跳着”的问题
            # 分时图请求数据量
            # SGE: 约 660min; INTL: 约 1440min
            lmt = "1500"
        else:
            klt = "101"
            # 日K线显示最近5个月 (约100个交易日)
            lmt = "100"
        
        if symbol == "hf_GC":
            url = EASTMONEY_KLINE_INTL.format(klt=klt, lmt=lmt)
        else:
            url = EASTMONEY_KLINE_DOM.format(klt=klt, lmt=lmt)
            
        self._load_kline_data(symbol, url)

    def _load_kline_data(self, symbol, url):
        """
        使用 curl_cffi 模拟 Edge 浏览器指纹获取数据。
        这是目前绕过东方财富 TLS 指纹校验最有效的方法。
        """
        mode = self.view_modes.get(symbol, "realtime")
        max_retries = 2
        
        # 模拟完整的浏览器 Header 顺序和内容
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://quote.eastmoney.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }

        for attempt in range(max_retries + 1):
            try:
                # 使用 curlex (即 curl_cffi.requests) 模拟 chrome100 指纹
                # 禁用代理以防干扰，设置较长的超时（20秒）以应对 DNS 解析慢的问题
                resp = curlex.get(url, headers=headers, impersonate="chrome100", timeout=20, verify=False)
                
                if resp.status_code == 200 and resp.text:
                    data = resp.json()
                    if data and "data" in data and data["data"] and "klines" in data["data"]:
                        klines = data["data"]["klines"]
                        kline_items = []
                        for k in klines:
                            parts = k.split(',')
                            if len(parts) >= 6:
                                # 基础字段：日期, 开, 收, 高, 低, 量
                                d_str = parts[0]
                                o_p = float(parts[1])
                                c_p = float(parts[2])
                                h_p = float(parts[3])
                                l_p = float(parts[4])
                                v_p = float(parts[5])
                                
                                # 特殊处理 COMEX 黄金 (hf_GC) 的日 K 线: 将“收”改为“结算数据” (f65)
                                if "hf_GC" in symbol and mode == "daily" and len(parts) > 8:
                                    settlement = float(parts[8])
                                    if settlement > 0:
                                        c_p = settlement
                                
                                kline_items.append((d_str, o_p, c_p, h_p, l_p, v_p))
                        
                        if kline_items:
                            kline_widget = self.findChild(InteractiveKLine, f"{symbol}_kline")
                            if kline_widget:
                                prev_close = self.last_prices.get(symbol)
                                kline_widget.update_data(kline_items, prev_close)
                            return # 成功获取数据，直接返回
                else:
                    print(f"curl_cffi attempt {attempt+1} failed for {symbol}: {resp.status_code}")
                    
            except Exception as e:
                if attempt < max_retries:
                    print(f"Attempt {attempt+1} failed for {symbol} due to timeout/error: {e}. Retrying in 1s...")
                    time.sleep(1)
                else:
                    print(f"Detail load kline data error via curl_cffi for {symbol} after {max_retries+1} attempts: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

class GoldViewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_pos = None
        self.init_ui()
        self.detail_window = DetailWindow(self)
        self.start_fetcher()
        self.init_tray()

    def init_ui(self):
        # 无边框、窗口置顶、不显示在任务栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 设置固定大小，再次调大以满足大屏或高清晰度展示需求
        self.setWindowTitle("金价看板")
        self.setFixedSize(320, 280)
        self.setWindowIcon(self.create_tray_icon())
        
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 容器框架
        self.container = QFrame()
        self.container.setObjectName("mainContainer")
        self.container.setStyleSheet("""
            QFrame#mainContainer {
                background-color: rgba(25, 25, 25, 220);
                border: 1px solid rgba(255, 215, 0, 60);
                border-radius: 12px;
            }
        """)
        layout.addWidget(self.container)

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        
        # 顶部状态栏
        top_bar = QHBoxLayout()
        self.time_label = QLabel("更新于 ----- --:--:--")
        self.time_label.setStyleSheet("color: rgba(255, 255, 255, 120); font-size: 11px; font-family: 'Segoe UI'; min-width: 150px;")
        
        self.expand_btn = QPushButton("❐")
        self.expand_btn.setFixedSize(20, 20)
        self.expand_btn.setToolTip("查看详情图表")
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { color: #FFD700; background-color: rgba(255, 255, 255, 15); border-radius: 4px; }
        """)
        self.expand_btn.clicked.connect(self.show_detail)
        
        top_bar.addWidget(self.time_label)
        top_bar.addStretch()
        top_bar.addWidget(self.expand_btn)
        self.content_layout.addLayout(top_bar)

        # 国际金价卡片
        self.intl_card = self.create_price_row("COMEX 黄金 GC", "intl")
        self.content_layout.addLayout(self.intl_card)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 15);")
        self.content_layout.addWidget(line)

        # 国内金价卡片
        self.dom_card = self.create_price_row("国内 AU9999", "au9999")
        self.content_layout.addLayout(self.dom_card)

        self.update_position()

    def create_price_row(self, title, key):
        row = QVBoxLayout()
        row.setSpacing(4)
        
        # 1. 顶部状态行
        status_hbox = QHBoxLayout()
        status_hbox.setSpacing(6)
        status_dot = QLabel("●")
        status_dot.setObjectName(f"{key}_status_dot")
        status_dot.setStyleSheet("color: #4CAF50; font-size: 10px;")
        
        status_text = QLabel("交易中")
        status_text.setObjectName(f"{key}_status_text")
        status_text.setStyleSheet("color: rgba(255, 255, 255, 150); font-size: 11px; font-weight: 500; font-family: 'Microsoft YaHei';")
        
        status_hbox.addWidget(status_dot)
        status_hbox.addWidget(status_text)
        status_hbox.addStretch()
        row.addLayout(status_hbox)
        
        # 2. 标题与昨收行
        title_hbox = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #FFD700; font-size: 15px; font-weight: bold; font-family: 'Microsoft YaHei'; letter-spacing: 1px;")
        
        # 昨收显示更醒目
        prev_lbl = QLabel("昨收: --")
        prev_lbl.setObjectName(f"{key}_prev")
        prev_lbl.setStyleSheet("color: #E0E0E0; font-size: 12px; font-weight: 500; font-family: 'Segoe UI'; border-bottom: 1px dashed rgba(255, 255, 255, 40); padding-bottom: 1px;")
        
        title_hbox.addWidget(title_lbl)
        title_hbox.addStretch()
        title_hbox.addWidget(prev_lbl)
        row.addLayout(title_hbox)
        
        # 3. 价格与涨跌幅行
        price_hbox = QHBoxLayout()
        price_hbox.setContentsMargins(0, 2, 0, 0)
        
        price_lbl = QLabel("--")
        price_lbl.setObjectName(f"{key}_price")
        price_lbl.setStyleSheet("color: #FFFFFF; font-size: 42px; font-weight: 700; font-family: 'Segoe UI Semibold', 'Impact';")
        
        change_lbl = QLabel("-- / --")
        change_lbl.setObjectName(f"{key}_change")
        change_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        change_lbl.setStyleSheet("color: #CCCCCC; font-size: 15px; font-weight: 600; font-family: 'Segoe UI'; margin-bottom: 8px;")
        
        price_hbox.addWidget(price_lbl)
        price_hbox.addStretch()
        price_hbox.addWidget(change_lbl)
        row.addLayout(price_hbox)
        
        return row

    def show_detail(self):
        self.hide()
        self.detail_window.show_and_fetch()
        # 立即强制刷新一次大窗 K 线
        self.detail_window.update_klines()

    def update_position(self):
        # 获取主屏幕的可用区域（自动避开任务栏）
        screen_geo = QApplication.primaryScreen().availableGeometry()
        
        # 贴近右侧边缘但保留极小间距（从 15px 减小到 5px）
        margin_right = 5
        margin_top = 60
        
        x = screen_geo.right() - self.width() - margin_right
        y = screen_geo.top() + margin_top
        
        self.move(x, y)

    def update_prices(self, data):
        # 使用数据中自带的时间戳，确保只有成功更新后 UI 时间才变化
        refresh_time = data.get("time", "--:--:--")
        if refresh_time != "--:--:--":
            self.time_label.setText(f"更新于 {refresh_time}")
        
        # 国际
        intl = data.get("intl")
        if intl:
            p_lbl = self.findChild(QLabel, "intl_price")
            c_lbl = self.findChild(QLabel, "intl_change")
            prev_lbl = self.findChild(QLabel, "intl_prev")
            dot_lbl = self.findChild(QLabel, "intl_status_dot")
            st_lbl = self.findChild(QLabel, "intl_status_text")
            
            # 红涨绿跌颜色
            change_val = float(intl['change']) if isinstance(intl['change'], (int, float)) else 0
            if isinstance(intl['change'], str):
                try: change_val = float(intl['change'].replace('+', ''))
                except: pass
            color = "#FF5252" if change_val > 0 else "#4CAF50" if change_val < 0 else "#FFF"
            
            if p_lbl: 
                p_lbl.setText(f"${intl['price']}")
                p_lbl.setStyleSheet(f"color: {color}; font-size: 42px; font-weight: 700; font-family: 'Segoe UI Semibold', 'Impact';")
            if c_lbl: 
                c_lbl.setText(f"{intl['change']} / {intl['percent']}")
                self.apply_trend_color(c_lbl, intl['change'])
            if prev_lbl: prev_lbl.setText(f"昨收: {intl['prev']}")
            
            is_open = intl.get("open_status", False)
            data_time = intl.get("data_time", "")
            if dot_lbl:
                dot_lbl.setStyleSheet(f"color: {'#4CAF50' if is_open else '#888'}; font-size: 8px;")
            if st_lbl:
                status_text = "交易中" if is_open else "已收盘"
                if data_time:
                    st_lbl.setText(f"{status_text} ({data_time})")
                else:
                    st_lbl.setText(status_text)
                st_lbl.setStyleSheet(f"color: {'#4CAF50' if is_open else 'rgba(255, 255, 255, 130)'}; font-size: 11px; font-weight: bold;")
        
        # 国内
        au = data.get("au9999")
        if au:
            # 如果国内已收盘且有数据时间，则在状态栏显示该时间
            is_open = au.get("open_status", False)
            is_pause = au.get("pause_status", False)
            data_time = au.get("data_time", "")
            
            p_lbl = self.findChild(QLabel, "au9999_price")
            c_lbl = self.findChild(QLabel, "au9999_change")
            prev_lbl = self.findChild(QLabel, "au9999_prev")
            dot_lbl = self.findChild(QLabel, "au9999_status_dot")
            st_lbl = self.findChild(QLabel, "au9999_status_text")
            
            change_val = float(au['change']) if isinstance(au['change'], (int, float)) else 0
            if isinstance(au['change'], str):
                try: change_val = float(au['change'].replace('+', ''))
                except: pass
            color = "#FF5252" if change_val > 0 else "#4CAF50" if change_val < 0 else "#FFF"
            
            if p_lbl: 
                p_lbl.setText(f"¥{au['price']}")
                p_lbl.setStyleSheet(f"color: {color}; font-size: 42px; font-weight: 700; font-family: 'Segoe UI Semibold', 'Impact';")
            if c_lbl: 
                c_lbl.setText(f"{au['change']} / {au['percent']}")
                self.apply_trend_color(c_lbl, au['change'])
            if prev_lbl: prev_lbl.setText(f"昨收: {au['prev']}")
            
            if dot_lbl:
                dot_clr = '#4CAF50' if is_open else '#FF9800' if is_pause else '#888'
                dot_lbl.setStyleSheet(f"color: {dot_clr}; font-size: 8px;")
            if st_lbl:
                if is_open:
                    txt, clr = "交易中", '#4CAF50'
                elif is_pause:
                    txt, clr = "盘中休市", '#FF9800'
                else:
                    txt, clr = "已收盘", 'rgba(255, 255, 255, 130)'
                
                if data_time:
                    st_lbl.setText(f"{txt} ({data_time})")
                else:
                    st_lbl.setText(txt)
                st_lbl.setStyleSheet(f"color: {clr}; font-size: 11px; font-weight: bold;")
        
        # 数据更新后，不再调用 update_position()，防止位置跳动

    def apply_trend_color(self, label, change_str):
        color = "#FF5252" if '+' in change_str else "#4CAF50" if '-' in change_str else "#AAA" # 红涨绿跌
        label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; font-family: 'Segoe UI';")

    def create_tray_icon(self):
        # 处理 PyInstaller 打包后的路径
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "app_icon.png")
        else:
            icon_path = "app_icon.png"
            
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        
        # 如果文件不存在，回退到原来的绘制逻辑
        pixmap = QPixmap(128, 128)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. 绘制底座阴影 (Shadow)
        painter.setBrush(QColor(0, 0, 0, 60))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(15, 85, 98, 20, 10, 10)
        
        # 2. 绘制金砖侧面 (Body/Side)
        side_gradient = QLinearGradient(0, 0, 128, 128)
        side_gradient.setColorAt(0, QColor(218, 165, 32)) # GoldenRod
        side_gradient.setColorAt(1, QColor(139, 101, 8))  # Darker
        painter.setBrush(side_gradient)
        
        body_path = QPainterPath()
        body_path.moveTo(20, 40)   # 左上
        body_path.lineTo(108, 40)  # 右上
        body_path.lineTo(120, 100) # 右下
        body_path.lineTo(8, 100)   # 左下
        body_path.closeSubpath()
        painter.drawPath(body_path)
        
        # 3. 绘制顶部平面 (Top Surface)
        top_gradient = QLinearGradient(20, 40, 108, 100)
        top_gradient.setColorAt(0, QColor(255, 255, 150)) # Very light
        top_gradient.setColorAt(0.5, QColor(255, 215, 0)) # Gold
        top_gradient.setColorAt(1, QColor(218, 165, 32))  # GoldenRod
        painter.setBrush(top_gradient)
        
        top_path = QPainterPath()
        top_path.moveTo(30, 45)  # 左上
        top_path.lineTo(98, 45)  # 右上
        top_path.lineTo(105, 85) # 右下
        top_path.lineTo(23, 85)  # 左下
        top_path.closeSubpath()
        painter.drawPath(top_path)
        
        # 4. 绘制文字 "AU"
        painter.setPen(QColor(139, 101, 8, 200)) # 深色阴影字
        font = QFont("Impact", 32)
        painter.setFont(font)
        # 稍微偏移一点点做阴影
        painter.drawText(pixmap.rect().adjusted(2, 2, 2, 2), Qt.AlignmentFlag.AlignCenter, "AU")
        
        painter.setPen(QColor(101, 67, 33)) # 棕色文字
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "AU")
        
        # 5. 绘制文字下方的小字 "999.9"
        small_font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(small_font)
        painter.drawText(pixmap.rect().adjusted(0, 45, 0, 45), Qt.AlignmentFlag.AlignCenter, "999.9")
        
        # 6. 添加光泽闪烁 (Sparkles)
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(35, 50, 4, 4)
        painter.drawEllipse(90, 75, 3, 3)
        
        painter.end()
        return QIcon(pixmap)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.create_tray_icon())
        self.tray_icon.setToolTip("金价看板")
        
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: white; border: 1px solid #444; } QMenu::item:selected { background-color: #3d3d3d; }")
        
        refresh_action = QAction("手动刷新", self)
        refresh_action.triggered.connect(self.manual_refresh)
        
        autostart_action = QAction("开机自启动", self)
        autostart_action.setCheckable(True)
        autostart_action.setChecked(self.is_autostart_enabled())
        autostart_action.triggered.connect(self.toggle_autostart)
        
        exit_action = QAction("退出程序", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        
        menu.addAction(refresh_action)
        menu.addAction(autostart_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def start_fetcher(self):
        self.fetcher = PriceFetcher()
        self.fetcher.price_updated.connect(self.update_prices)
        self.fetcher.start()
        # 启动后立即触发一次获取，确保初始化时有数据
        self.fetcher.trigger_fetch()

    def manual_refresh(self):
        """手动刷新逻辑：根据当前窗口状态刷新全部数据"""
        if hasattr(self, 'detail_window') and self.detail_window.isVisible():
            # 大窗模式：触发大窗的数据获取和 K 线更新
            self.detail_window.fetch_detail_data(force=True)
            self.detail_window.update_klines()
            self.detail_window.timer.start(10000)
        else:
            # 小窗模式：触发小窗的数据获取
            self.fetcher.trigger_fetch()

    def is_autostart_enabled(self):
        key_name = "GoldViewApp"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, key_name)
            winreg.CloseKey(key)
            return True
        except:
            return False

    def toggle_autostart(self, checked):
        app_path = os.path.abspath(sys.argv[0])
        key_name = "GoldViewApp"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if checked:
                pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
                winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, f'"{pythonw_path}" "{app_path}"')
            else:
                winreg.DeleteValue(key, key_name)
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Autostart toggle failed: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # 保证托盘运行时不退出
    
    widget = GoldViewWidget()
    app.setWindowIcon(widget.tray_icon.icon()) # 设置程序图标
    widget.show()
    
    sys.exit(app.exec())
