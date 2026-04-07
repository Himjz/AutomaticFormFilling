# main.py（补充多进程支持）
import sys
import os
import asyncio
import multiprocessing  # 新增
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

from core import submit_forms
from gui.main_window import MainWindow
from gui.tray_icon import TrayIcon
from gui.data_model import FormDataModel
from gui.scheduler import SubmitScheduler

# 全局事件循环
GLOBAL_LOOP = None

# 适配Windows多进程
if os.name == "nt":
    multiprocessing.freeze_support()

def get_icon_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "resource", "aff.ico")
    if not os.path.exists(icon_path):
        print(f"⚠️ 图标文件不存在：{icon_path}")
        return ""
    return icon_path

def init_asyncio_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def main():
    global GLOBAL_LOOP
    GLOBAL_LOOP = init_asyncio_loop()
    asyncio.set_event_loop(GLOBAL_LOOP)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    ICON_PATH = get_icon_path()
    if ICON_PATH:
        app.setWindowIcon(QIcon(ICON_PATH))

    data_model = FormDataModel()
    main_window = MainWindow(data_model)
    tray_icon = TrayIcon(main_window, ICON_PATH)
    tray_icon.setVisible(True)
    tray_icon.setToolTip("表单自动填写工具 - 预加载数据版")

    # 初始化调度器
    scheduler = SubmitScheduler(data_model)

    # 信号绑定
    tray_icon.open_editor.connect(main_window.show)
    tray_icon.quit_app.connect(app.quit)
    tray_icon.schedule_submit.connect(lambda: scheduler.open_dialog(main_window))

    scheduler.submit_finished.connect(lambda msg: QMessageBox.information(main_window, "提交成功", msg))
    scheduler.submit_error.connect(lambda err: QMessageBox.critical(main_window, "提交失败", err))

    # asyncio轮询（兼容Qt循环）
    def asyncio_poll():
        try:
            GLOBAL_LOOP.call_soon(GLOBAL_LOOP.stop)
            GLOBAL_LOOP.run_forever()
        except Exception:
            pass

    poll_timer = QTimer()
    poll_timer.setInterval(100)
    poll_timer.timeout.connect(asyncio_poll)
    poll_timer.start()

    # 启动提示
    QTimer.singleShot(500, lambda: tray_icon.showMessage(
        "启动成功",
        "程序已运行在系统托盘\n支持预加载数据+独立进程定时提交",
        QSystemTrayIcon.Information,
        3000
    ))

    print("✅ 程序启动成功（预加载数据版）")

    try:
        exit_code = app.exec()
    finally:
        # 程序退出清理
        poll_timer.stop()
        GLOBAL_LOOP.close()
        scheduler.cleanup()  # 清理调度器资源
        print("🏁 程序已安全退出，所有进程/线程已销毁")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()