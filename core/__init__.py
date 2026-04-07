import asyncio
from core.core import FormCore


def submit_forms(url: str, data_list: list[dict], headless: bool = True, max_concurrent: int = 3):
    """
    后台批量提交表单（默认无浏览器窗口）

    Args:
        url: 表单页面完整URL
        data_list: 提交数据列表（每个元素是包含表单字段的字典，字段需包含：学号/专业班级/姓名/联系方式/QQ号）
        headless: 是否无头模式（默认True，完全后台运行；False显示浏览器）
        max_concurrent: 最大并发数（默认3，避免并发过高导致异常）

    Raises:
        ValueError: 参数格式验证失败时抛出
        Exception: 执行过程中异常（如页面加载失败、提交失败等）
    """
    # 严格参数校验
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url必须是非空的字符串")
    if not isinstance(data_list, list) or len(data_list) == 0:
        raise ValueError("data_list必须是非空的字典列表")
    for idx, item in enumerate(data_list):
        if not isinstance(item, dict):
            raise ValueError(f"data_list第{idx + 1}个元素不是字典类型")
        # 校验必填字段
        required_fields = {"学号", "专业班级", "姓名", "联系方式", "QQ号"}
        missing_fields = required_fields - item.keys()
        if missing_fields:
            raise ValueError(f"data_list第{idx + 1}个元素缺少必填字段：{missing_fields}")
    if not isinstance(max_concurrent, int) or max_concurrent < 1:
        raise ValueError("max_concurrent必须是大于0的整数")

    # 异步核心逻辑
    async def main():
        main_core = FormCore(headless=headless)
        try:
            await main_core.start()
            await main_core.run_concurrent(url, data_list, max_tasks=max_concurrent)
        finally:
            await main_core.close()

    # 执行异步任务
    asyncio.run(main())


# 仅暴露submit_forms函数，无其他冗余代码、无示例调用
__all__ = ["submit_forms"]