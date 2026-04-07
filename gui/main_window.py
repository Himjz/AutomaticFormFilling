from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QLineEdit, QLabel, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import os
from gui.data_model import FormDataModel, FormData

ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "aff.ico")

class MainWindow(QMainWindow):
    def __init__(self, model: FormDataModel):
        super().__init__()
        self.model = model
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        self.setWindowTitle("表单自动填写工具 - 数据管理")
        self.setFixedSize(800, 500)
        self.setWindowIcon(QIcon(ICON_PATH))
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        input_layout = QHBoxLayout()
        self.edit_student_id = self.add_input("学号", input_layout)
        self.edit_name = self.add_input("姓名", input_layout)
        self.edit_class = self.add_input("班级", input_layout)
        self.edit_phone = self.add_input("电话", input_layout)
        self.edit_qq = self.add_input("QQ", input_layout)
        layout.addLayout(input_layout)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("新增")
        self.btn_update = QPushButton("修改")
        self.btn_delete = QPushButton("删除")
        self.btn_clear = QPushButton("清空输入")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "学号", "姓名", "班级", "电话", "QQ"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self.add_data)
        self.btn_update.clicked.connect(self.update_data)
        self.btn_delete.clicked.connect(self.delete_data)
        self.btn_clear.clicked.connect(self.clear_input)
        self.table.cellClicked.connect(self.on_table_click)

    def add_input(self, label_text, layout):
        layout.addWidget(QLabel(label_text))
        edit = QLineEdit()
        layout.addWidget(edit)
        return edit

    def refresh_table(self):
        data_list = self.model.get_all()
        self.table.setRowCount(len(data_list))
        for row, item in enumerate(data_list):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.id)))
            self.table.setItem(row, 1, QTableWidgetItem(item.student_id))
            self.table.setItem(row, 2, QTableWidgetItem(item.name))
            self.table.setItem(row, 3, QTableWidgetItem(item.classes))
            self.table.setItem(row, 4, QTableWidgetItem(item.phone))
            self.table.setItem(row, 5, QTableWidgetItem(item.qq))
            self.table.item(row, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def on_table_click(self, row, col):
        data_id = int(self.table.item(row, 0).text())
        data = self.model.get_by_id(data_id)
        if data:
            self.edit_student_id.setText(data.student_id)
            self.edit_name.setText(data.name)
            self.edit_class.setText(data.classes)
            self.edit_phone.setText(data.phone)
            self.edit_qq.setText(data.qq)
            self.current_edit_id = data_id

    def add_data(self):
        if not all([self.edit_student_id.text(), self.edit_name.text()]):
            QMessageBox.warning(self, "提示", "学号和姓名不能为空！")
            return
        self.model.add_data(
            self.edit_student_id.text(),
            self.edit_name.text(),
            self.edit_class.text(),
            self.edit_phone.text(),
            self.edit_qq.text()
        )
        self.refresh_table()
        self.clear_input()
        QMessageBox.information(self, "成功", "新增数据完成！")

    def update_data(self):
        if not hasattr(self, "current_edit_id"):
            QMessageBox.warning(self, "提示", "请先选择要修改的数据！")
            return
        self.model.update_data(
            self.current_edit_id,
            self.edit_student_id.text(),
            self.edit_name.text(),
            self.edit_class.text(),
            self.edit_phone.text(),
            self.edit_qq.text()
        )
        self.refresh_table()
        QMessageBox.information(self, "成功", "修改数据完成！")

    def delete_data(self):
        if not hasattr(self, "current_edit_id"):
            QMessageBox.warning(self, "提示", "请先选择要删除的数据！")
            return
        self.model.delete_data(self.current_edit_id)
        self.refresh_table()
        self.clear_input()
        QMessageBox.information(self, "成功", "删除数据完成！")

    def clear_input(self):
        self.edit_student_id.clear()
        self.edit_name.clear()
        self.edit_class.clear()
        self.edit_phone.clear()
        self.edit_qq.clear()
        if hasattr(self, "current_edit_id"):
            del self.current_edit_id

    # 关闭窗口最小化到托盘，不退出
    def closeEvent(self, event):
        self.hide()
        event.ignore()