# gui/scheduler.py（最终版：预加载数据+解耦倒计时+进程等待）
import asyncio
import threading
import time
import multiprocessing
from typing import Optional, List, Dict
from datetime import datetime

from PySide6.QtCore import QTimer, QTime, QDateTime, Signal, QObject, Qt, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTimeEdit, QMessageBox

from core import submit_forms
from utils.config import ASYNC_CONFIG, FORM_CONFIG


# 全局获取运行中的事件循环
def get_running_loop():
    """安全获取当前运行的事件循环"""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


# 进程间通信：用于传递预加载的数据
def task_worker(target_timestamp: float, preloaded_data: List[Dict], result_queue: multiprocessing.Queue):
    """独立进程等待函数（仅等待，不处理UI）"""
    try:
        # 后台等待，直到到达目标时间
        while time.time() < target_timestamp:
            time.sleep(1)  # 每秒检查一次，低资源消耗

        # 到达时间后执行提交
        if asyncio.iscoroutinefunction(submit_forms):
            # 异步函数需在进程内创建循环执行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                submit_forms(
                    url=FORM_CONFIG["url"],
                    data_list=preloaded_data,
                    headless=FORM_CONFIG.get("headless", False),
                    max_concurrent=ASYNC_CONFIG["max_concurrent"]
                )
            )
            loop.close()
        else:
            # 同步函数直接执行
            result = submit_forms(
                url=FORM_CONFIG["url"],
                data_list=preloaded_data,
                headless=FORM_CONFIG.get("headless", False),
                max_concurrent=ASYNC_CONFIG["max_concurrent"]
            )
        result_queue.put(("success", f"共处理 {len(preloaded_data)} 条数据"))
    except Exception as e:
        result_queue.put(("error", str(e)))


class ScheduleDialog(QDialog):
    """单次定时提交窗口（仅负责UI和倒计时展示）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("单次定时提交（预加载数据）")
        self.setFixedSize(400, 240)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignTop)

        # 标题
        title = QLabel("设置单次自动提交时间（定时后立即加载数据）")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 时间选择
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("目标时间："))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setFont(QFont("Microsoft YaHei", 11))
        time_layout.addWidget(self.time_edit)
        layout.addLayout(time_layout)

        # 数据状态提示
        self.data_status_label = QLabel("📥 未加载数据")
        self.data_status_label.setFont(QFont("Microsoft YaHei", 10))
        self.data_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.data_status_label)

        # 倒计时（仅UI展示，无业务逻辑）
        self.countdown_label = QLabel("⏱ 未设置定时任务")
        self.countdown_label.setFont(QFont("Microsoft YaHei", 10))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.countdown_label)

        # 按钮
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始单次定时")
        self.btn_stop = QPushButton("取消定时")
        self.btn_close = QPushButton("关闭窗口")
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def get_target_time(self) -> QTime:
        return self.time_edit.time()

    def update_data_status(self, data_count: int):
        """更新预加载数据状态"""
        if data_count == 0:
            self.data_status_label.setText("⚠️ 预加载数据为空")
        else:
            self.data_status_label.setText(f"✅ 已预加载 {data_count} 条数据")

    def update_countdown(self, remaining: Optional[int]):
        """仅更新倒计时展示，不影响执行"""
        if remaining is None:
            self.countdown_label.setText("⏱ 未设置定时任务")
        elif remaining <= 0:
            self.countdown_label.setText("🚀 正在执行提交...")
        else:
            h, m, s = remaining // 3600, (remaining % 3600) // 60, remaining % 60
            self.countdown_label.setText(f"⏱ 剩余：{h:02d}:{m:02d}:{s:02d}")


class SubmitScheduler(QObject):
    submit_finished = Signal(str)
    submit_error = Signal(str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.dialog: Optional[ScheduleDialog] = None

        # UI倒计时定时器（仅展示，无业务逻辑）
        self.count_timer = QTimer(self)
        self.count_timer.setInterval(100)
        self.count_timer.timeout.connect(self._update_countdown)

        # 进程相关
        self.task_process: Optional[multiprocessing.Process] = None
        self.result_queue = multiprocessing.Queue()  # 进程间结果通信
        self.target_dt: Optional[QDateTime] = None
        self.preloaded_data: List[Dict] = []  # 预加载的数据

        # 结果监听线程（监听进程执行结果）
        self.result_thread: Optional[threading.Thread] = None
        self._running = False

    def open_dialog(self, parent=None):
        """打开定时配置窗口"""
        self.stop_schedule()
        self.dialog = ScheduleDialog(parent)
        self.dialog.btn_start.clicked.connect(self._start_single_schedule)
        self.dialog.btn_stop.clicked.connect(self.stop_schedule)
        self.dialog.btn_close.clicked.connect(self._close_dialog)
        self.dialog.exec()

    def _preload_data(self):
        """定时后立即预加载数据（UI线程执行，仅读取数据）"""
        self.preloaded_data.clear()
        try:
            # 读取所有数据并转换格式（立即完成，不等待）
            data_list = self.model.get_all()
            for data in data_list:
                self.preloaded_data.append({
                    "学号": data.student_id,
                    "专业班级": data.classes,
                    "姓名": data.name,
                    "联系方式": data.phone,
                    "QQ号": data.qq
                })
            # 更新UI数据状态
            if self.dialog:
                self.dialog.update_data_status(len(self.preloaded_data))
            print(f"📥 预加载完成：{len(self.preloaded_data)} 条数据")
        except Exception as e:
            if self.dialog:
                self.dialog.update_data_status(0)
            print(f"❌ 数据预加载失败：{str(e)}")

    def _start_single_schedule(self):
        """启动单次定时任务：预加载数据 → 启动进程等待 → UI倒计时"""
        if self.task_process and self.task_process.is_alive():
            QMessageBox.warning(self.dialog, "提示", "已有单次定时任务运行中！")
            return

        # 1. 立即预加载数据（核心：定时后马上准备好数据）
        self._preload_data()
        if not self.preloaded_data:
            QMessageBox.warning(self.dialog, "警告", "预加载数据为空，无法启动定时任务！")
            return

        # 2. 计算目标时间和时间戳
        target_time = self.dialog.get_target_time()
        now = QDateTime.currentDateTime()
        target_dt = QDateTime(now.date(), target_time)
        if target_dt < now:
            target_dt = target_dt.addDays(1)
            QMessageBox.information(self.dialog, "提示",
                                    f"所选时间已过，自动顺延至次日 {target_time.toString('HH:mm:ss')}")

        self.target_dt = target_dt
        target_timestamp = target_dt.toSecsSinceEpoch()  # 转换为Unix时间戳

        # 3. 启动独立进程等待执行（与UI完全解耦）
        self.task_process = multiprocessing.Process(
            target=task_worker,
            args=(target_timestamp, self.preloaded_data, self.result_queue),
            daemon=True  # 进程随主线程退出
        )
        self.task_process.start()

        # 4. 启动结果监听线程
        self._running = True
        self.result_thread = threading.Thread(target=self._listen_result, daemon=True)
        self.result_thread.start()

        # 5. 启动UI倒计时（仅展示，不影响进程）
        self.count_timer.start()
        self.dialog.btn_start.setEnabled(False)

        QMessageBox.information(
            self.dialog, "成功",
            f"✅ 单次定时任务已启动\n📥 已预加载 {len(self.preloaded_data)} 条数据\n⏰ 将在 {target_dt.toString('yyyy-MM-dd HH:mm:ss')} 执行提交"
        )

    def _listen_result(self):
        """监听进程执行结果（独立线程，不阻塞UI）"""
        while self._running:
            if not self.result_queue.empty():
                # 获取进程执行结果
                result_type, msg = self.result_queue.get()
                if result_type == "success":
                    self.submit_finished.emit(f"✅ 单次提交完成！{msg}")
                else:
                    self.submit_error.emit(f"❌ 单次提交失败：{msg}")
                # 结果处理完成后停止监听
                self._running = False
                break
            time.sleep(0.5)

    def _update_countdown(self):
        """仅更新UI倒计时，与进程等待逻辑完全解耦"""
        if not self.target_dt or not self.dialog:
            return
        remaining = QDateTime.currentDateTime().secsTo(self.target_dt)
        self.dialog.update_countdown(remaining)

    async def _do_submit(self):
        """兼容异步提交的兜底逻辑"""
        try:
            if asyncio.iscoroutinefunction(submit_forms):
                await submit_forms(
                    url=FORM_CONFIG["url"],
                    data_list=self.preloaded_data,
                    headless=FORM_CONFIG.get("headless", False),
                    max_concurrent=ASYNC_CONFIG["max_concurrent"]
                )
            else:
                loop = get_running_loop()
                await loop.run_in_executor(
                    None,
                    lambda: submit_forms(
                        url=FORM_CONFIG["url"],
                        data_list=self.preloaded_data,
                        headless=FORM_CONFIG.get("headless", False),
                        max_concurrent=ASYNC_CONFIG["max_concurrent"]
                    )
                )
        except Exception as e:
            raise e

    def stop_schedule(self):
        """停止所有任务（进程+线程+UI倒计时）"""
        # 1. 停止结果监听线程
        self._running = False

        # 2. 终止后台进程
        if self.task_process and self.task_process.is_alive():
            self.task_process.terminate()
            self.task_process.join(2)  # 等待进程退出
        self.task_process = None

        # 3. 停止UI倒计时（仅展示层）
        self.count_timer.stop()

        # 4. 清空状态
        self.target_dt = None
        self.preloaded_data.clear()

        # 5. 重置UI
        if self.dialog:
            self.dialog.btn_start.setEnabled(True)
            self.dialog.update_countdown(None)
            self.dialog.update_data_status(0)

        print("🛑 定时任务已手动停止，所有进程/线程已清理")

    def _close_dialog(self):
        """安全关闭窗口"""
        self.stop_schedule()
        if self.dialog:
            self.dialog.close()
            self.dialog = None

    def cleanup(self):
        """程序退出时的资源清理"""
        self.stop_schedule()
        # 清空结果队列
        while not self.result_queue.empty():
            self.result_queue.get()


# 适配Windows多进程启动（必须）
if __name__ == "__main__":
    multiprocessing.freeze_support()