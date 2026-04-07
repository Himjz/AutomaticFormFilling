from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal

class TrayIcon(QSystemTrayIcon):
    # 信号
    open_editor = Signal()    # 打开数据编辑
    schedule_submit = Signal() # 定时提交
    quit_app = Signal()

    def __init__(self, parent=None, icon_path=""):
        super().__init__(parent)
        self.setIcon(QIcon(icon_path))
        self.setToolTip("表单自动填写工具")

        # 托盘菜单
        menu = QMenu(parent)
        self.open_action = QAction("修改提交数据", parent)
        self.schedule_action = QAction("定时提交", parent)
        self.quit_action = QAction("退出程序", parent)

        menu.addAction(self.open_action)
        menu.addAction(self.schedule_action)
        menu.addAction(self.quit_action)
        self.setContextMenu(menu)

        # 绑定
        self.open_action.triggered.connect(self.open_editor.emit)
        self.schedule_action.triggered.connect(self.schedule_submit.emit)
        self.quit_action.triggered.connect(self.quit_app.emit)
        self.activated.connect(self.on_double_click)

    def on_double_click(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.open_editor.emit()