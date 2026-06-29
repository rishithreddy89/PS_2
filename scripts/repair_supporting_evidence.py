import asyncio
import json
import logging
from sqlalchemy import select, update
from app.database.session import AsyncSessionLocal
from app.models.recommendation import Recommendation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def repair_supporting_evidence():
    logger.info("Starting database repair script for supporting_evidence...")
    
    async with AsyncSessionLocal() as session:
        # Fetch all recommendations
        stmt = select(Recommendation)
        result = await session.execute(stmt)
        recommendations = result.scalars().all()
        
        fixed_count = 0
        total_count = len(recommendations)
        
        for rec in recommendations:
            ev = rec.supporting_evidence
            needs_fix = False
            
            # If it's a string, try to parse it
            if isinstance(ev, str):
                try:
                    ev = json.loads(ev)
                    needs_fix = True
                except:
                    ev = []
                    needs_fix = True
            
            # Now `ev` should be None, dict, or list
            if ev is None:
                ev = []
                needs_fix = True
            elif isinstance(ev, dict):
                if "items" in ev:
                    ev = ev["items"]
                    if not isinstance(ev, list):
                        ev = []
                else:
                    ev = []
                needs_fix = True
            elif not isinstance(ev, list):
                # If it's somehow not a list, wrap it
                ev = [ev]
                needs_fix = True
                
            if needs_fix:
                logger.info(f"Fixing recommendation {rec.id}")
                rec.supporting_evidence = ev
                fixed_count += 1
                
        if fixed_count > 0:
            logger.info(f"Committing {fixed_count} fixes...")
            await session.commit()
        else:
            logger.info("No records needed fixing.")
            
        logger.info(f"Finished checking {total_count} records. Repaired: {fixed_count}")

if __name__ == "__main__":
    asyncio.run(repair_supporting_evidence())
