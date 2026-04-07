import unittest

from core.core import FormCore


class TestSingleSubmit(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """测试前启动浏览器"""
        self.form_url = "https://f.wps.cn/ksform/w/write/9ZhYHYlD"  # 换成你的真实地址
        self.core = FormCore(headless=False)
        await self.core.start()

    async def test_single_submit_success(self):
        """测试单任务自动提交"""
        test_data = {
            "学号": "S001",
            "专业班级": "软件测试班",
            "姓名": "单提交测试",
            "联系方式": "13800000001",
            "QQ号": "10001",
        }

        # 执行提交
        await self.core.run_task(self.form_url, test_data)

        # 断言：无异常抛出即成功
        self.assertTrue(True, "单提交执行完成")

    async def asyncTearDown(self):
        """测试后关闭浏览器"""
        await self.core.close()

if __name__ == '__main__':
    unittest.main()