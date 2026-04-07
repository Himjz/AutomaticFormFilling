import asyncio

from playwright.async_api import async_playwright, Page


class FormCore:
    def __init__(self, headless: bool = True):
        """
        自动填表核心（极速填写 + 确认后延时1秒）
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None

        # 表单字段配置
        self.FIELD_MAP = {
            "学号": "学号",
            "专业班级": "专业班级",
            "姓名": "姓名",
            "联系方式": "联系方式",
            "QQ号": "QQ号",
        }
        self.SUBMIT_BTN = "button.src-components-write-footer-index__submitBtn"
        self.CONFIRM_BTN = "div.ant-modal-footer button:has-text('确 认')"

    async def start(self):
        """启动浏览器（仅启动一次）"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        self.context = await self.browser.new_context(no_viewport=True)
        print("✅ 浏览器启动成功")

    async def create_page(self, url: str) -> Page:
        """打开页面（无多余延时）"""
        page = await self.context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=10000)
        print("🌍 页面已加载")
        return page

    async def fill_form(self, page: Page, data: dict):
        """极速填写（0 延时）"""
        print("\n" + "="*50)
        print("📝 极速填写表单")
        print("="*50)

        for key, value in data.items():
            if key not in self.FIELD_MAP:
                continue
            try:
                question = page.locator(".ksapc-questions-write-container", has_text=self.FIELD_MAP[key])
                await question.locator("textarea.ant-input").fill(value)
                print(f"✅ {key} → {value}")
            except:
                print(f"❌ {key} 填写失败")

        print("🎉 填写完成")

    async def submit_auto_confirm(self, page: Page):
        """提交 + 确认 + 确认后延时 1 秒"""
        try:
            # 点击提交
            await page.locator(self.SUBMIT_BTN).click()

            # 自动确认
            await page.wait_for_selector(self.CONFIRM_BTN, timeout=3000)
            await page.locator(self.CONFIRM_BTN).click()
            print("✅ 已确认提交")

            # 👉 确认后延时 1 秒再关闭（你要的效果）
            await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ 提交失败：{str(e)[:60]}")

    async def close(self):
        """关闭全部资源"""
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        print("\n🏁 浏览器已关闭")

    async def run_task(self, url: str, data: dict):
        """单任务执行"""
        page = await self.create_page(url)
        await self.fill_form(page, data)
        await self.submit_auto_confirm(page)
        await page.close()

    async def run_concurrent(self, url: str, data_list: list, max_tasks: int = 3):
        """并发控制"""
        semaphore = asyncio.Semaphore(max_tasks)
        async def task(data):
            async with semaphore:
                await self.run_task(url, data)
        await asyncio.gather(*[task(d) for d in data_list])