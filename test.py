# 从模块导入暴露的函数
from core import submit_forms

# 准备数据
form_url = "https://f.wps.cn/ksform/w/write/9ZhYHYlD"
form_data = [
    {
        "学号": "20240001",
        "专业班级": "计算机2401",
        "姓名": "张三",
        "联系方式": "13800138001",
        "QQ号": "123456789"
    },
    {
        "学号": "20240002",
        "专业班级": "计算机2401",
        "姓名": "李四",
        "联系方式": "13800138002",
        "QQ号": "987654321"
    }
]

submit_forms(form_url, form_data)