# gui/data_model.py
import json
from dataclasses import dataclass, asdict
from typing import List, Optional
from utils.config import DATA_FILE

@dataclass
class FormData:
    """纯数据类（无业务逻辑）"""
    id: int
    student_id: str
    name: str
    classes: str
    phone: str
    qq: str

class FormDataModel:
    """数据模型（仅做CRUD，无UI依赖）"""
    def __init__(self):
        self.data_list: List[FormData] = []
        self.load_data()

    def load_data(self):
        """加载数据"""
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self.data_list = [FormData(**item) for item in raw]
        except (FileNotFoundError, json.JSONDecodeError):
            self.data_list = []

    def save_data(self):
        """保存数据"""
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([asdict(d) for d in self.data_list], f, ensure_ascii=False, indent=2)

    # 以下为纯CRUD方法（无修改）
    def add_data(self, student_id, name, classes, phone, qq) -> FormData:
        new_id = max((d.id for d in self.data_list), default=0) + 1
        data = FormData(new_id, student_id, name, classes, phone, qq)
        self.data_list.append(data)
        self.save_data()
        return data

    def update_data(self, data_id, student_id, name, classes, phone, qq) -> bool:
        for d in self.data_list:
            if d.id == data_id:
                d.student_id = student_id
                d.name = name
                d.classes = classes
                d.phone = phone
                d.qq = qq
                self.save_data()
                return True
        return False

    def delete_data(self, data_id):
        self.data_list = [d for d in self.data_list if d.id != data_id]
        self.save_data()

    def get_all(self) -> List[FormData]:
        return self.data_list

    def get_by_id(self, data_id) -> Optional[FormData]:
        return next((d for d in self.data_list if d.id == data_id), None)