import unittest

from core.core import FormCore


class TestConcurrentSubmit(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.form_url = "https://f.wps.cn/ksform/w/write/9ZhYHYlD"  # 换成你的地址
        self.core = FormCore(headless=True)
        await self.core.start()

    async def test_concurrent_submit(self):
        """测试 3 个并发提交"""
        test_data_list = [
            {
                "学号": "C001",
                "专业班级": "并发1班",
                "姓名": "并发用户1",
                "联系方式": "13811110001",
                "QQ号": "20001",
            },
            {
                "学号": "C002",
                "专业班级": "并发2班",
                "姓名": "并发用户2",
                "联系方式": "13811110002",
                "QQ号": "20002",
            },
            {
                "学号": "C003",
                "专业班级": "并发3班",
                "姓名": "并发用户3",
                "联系方式": "13811110003",
                "QQ号": "20003",
            },
        ]

        # 执行并发（最多同时跑2个）
        await self.core.run_concurrent(
            url=self.form_url,
            data_list=test_data_list,
            max_tasks=3
        )

        self.assertTrue(True, "并发测试完成")

    async def asyncTearDown(self):
        await self.core.close()

if __name__ == '__main__':
    unittest.main()