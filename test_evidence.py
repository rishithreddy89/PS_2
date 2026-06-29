import numpy as np
np.float_ = np.float64
np.int_ = np.int64

import asyncio
from app.agents.evidence_agent import EvidenceAgent
from app.agents.context import ExecutionContext

async def main():
    agent = EvidenceAgent()
    context = ExecutionContext(case_id="5d67f6ad-7c72-40e1-a9be-6cd28c919abf")
    context.set_shared("retrieved_knowledge_text", "Some legal documents text.")
    context.input_data = {"query": "Test"}
    try:
        resp = await agent.execute(context)
        print(resp)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
