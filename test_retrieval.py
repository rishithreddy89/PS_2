import numpy as np
np.float_ = np.float64
np.int_ = np.int64

import asyncio
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.context import ExecutionContext

async def main():
    agent = RetrievalAgent()
    context = ExecutionContext(case_id="6c506067-a4af-469f-b6a9-9d786afe6fd0")
    context.input_data = {"query": "Test"}
    try:
        resp = await agent.execute(context)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
