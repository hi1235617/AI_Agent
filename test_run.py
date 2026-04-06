from nanobot import Nanobot
from nanobot.agent import AgentHook, AgentHookContext
import time

class TimingHook(AgentHook):
    def __init__(self):
        self.timings = {}  # 存储在实例上，不是 ctx.metadata
    
    async def before_iteration(self, ctx: AgentHookContext):
        # 记录开始时间，用 iteration 编号作为 key
        self.timings[ctx.iteration] = time.time()
        print(f">>> 开始迭代 {ctx.iteration}")
    
    async def after_iteration(self, ctx: AgentHookContext):
        
        t0 = self.timings.pop(ctx.iteration, None)
        if t0:
            elapsed = time.time() - t0
            print(f">>> 迭代 {ctx.iteration} 完成，耗时: {elapsed:.2f}s")
    
    async def before_execute_tools(self, ctx: AgentHookContext):
        # 这才是你真正想监控的工具调用
        for tc in ctx.tool_calls:
            print(f">>> 调用工具: {tc.name}({tc.arguments})")


class AuditHook(AgentHook):
    def __init__(self):
        self.calls = []
    
    async def before_execute_tools(self, ctx: AgentHookContext):
        for tc in ctx.tool_calls:
            self.calls.append(tc.name)
            print(f"工具调用: {tc.name} with args {tc.arguments}")


async def main():
    bot = Nanobot.from_config("C:\\Users\\lty\\.nanobot\\config.json")
    
    # 可以同时挂多个 hook
    timing_hook = TimingHook()
    audit_hook = AuditHook()
    
    result = await bot.run(
        "使用read_file工具读取E:/project2/AI_Agent/test_result/test.txt",
        hooks=[timing_hook, audit_hook]  # 两个都挂上
    )
    
    print(f"审计记录: {audit_hook.calls}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())