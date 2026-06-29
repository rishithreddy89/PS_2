# Specialized Agent Framework

This directory contains the specialized agent implementations for LexMind AI's Agentic Decision Intelligence Platform.

## Overview

Phase 3 introduces six specialized agents that perform structured data preparation without LLM dependencies. These agents are designed to be:

- **Domain-agnostic**: Work across Legal, Healthcare, Insurance, Finance, and other domains
- **Composable**: Can be chained together in workflows
- **Type-safe**: All inputs/outputs use Pydantic models
- **Observable**: Built-in logging, metrics, and health checks
- **Testable**: Comprehensive unit test coverage

## Agent Directory Structure

```
agents/
├── base.py                 # BaseAgent abstract class
├── context.py              # ExecutionContext for state management
├── planner.py              # PlannerAgent for workflow planning
├── orchestrator.py         # Orchestrator for agent execution
├── factory.py              # AgentFactory for agent creation
├── init.py                 # Agent initialization and registration
│
├── ingest_agent.py         # Document ingestion and normalization
├── retrieval_agent.py      # Retrieval request preparation
├── evidence_agent.py       # Evidence quality analysis
├── timeline_agent.py       # Timeline and deadline tracking
├── risk_agent.py           # Risk identification and assessment
├── memory_agent.py         # Memory interface management
│
└── sample_agents.py        # Sample agents (from Phase 2)
```

## Specialized Agents (Phase 3)

### 1. IngestAgent

**Purpose**: Ingest and normalize documents from various sources into a common structure.

**Capabilities**:
- `document_ingestion` - Accept documents in multiple formats
- `metadata_extraction` - Extract document metadata
- `entity_extraction` - Identify entities (people, organizations, dates)
- `event_extraction` - Extract events from content
- `normalization` - Convert to standard format

**Supported Document Types**:
- Case Notes
- Emails
- Meeting Notes
- Contracts
- Court Notices
- Witness Statements
- PDFs
- Plain Text

**Input**:
```python
{
    "content": "Document text...",
    "title": "Document Title",
    "type": "contract",  # or email, court_notice, etc.
    "source": "email",
    "file_type": "pdf"
}
```

**Output**: `DocumentSummary` with extracted entities, people, organizations, dates, and events.

### 2. RetrievalAgent

**Purpose**: Build structured retrieval requests for future RAG systems (does NOT perform RAG).

**Capabilities**:
- `query_building` - Construct semantic search queries
- `intent_detection` - Identify search intent
- `source_prioritization` - Rank knowledge sources
- `search_planning` - Plan retrieval strategy

**Search Intents**:
- Legal Research
- Precedent Search
- Statute Lookup
- Case History
- Internal Documents
- Playbooks

**Input**:
```python
{
    "query": "Find legal precedents for contract disputes",
    "case_type": "contract",
    "max_results": 10
}
```

**Output**: `RetrievalRequest` with intent, categories, prioritized sources.

### 3. EvidenceAgent

**Purpose**: Analyze evidence quality and identify gaps without legal reasoning.

**Capabilities**:
- `evidence_analysis` - Analyze evidence items
- `quality_assessment` - Assess evidence strength
- `gap_identification` - Identify missing evidence
- `conflict_detection` - Detect conflicting evidence
- `duplicate_detection` - Find duplicate evidence

**Evidence Quality Levels**:
- Strong
- Moderate
- Weak
- Insufficient

**Input**:
```python
{
    "evidence": [
        {
            "id": "ev1",
            "description": "Signed contract",
            "quality": "strong",
            "source": "original_document"
        }
    ],
    "required_evidence": ["Contract", "Payment records"]
}
```

**Output**: `EvidenceSummary` with categorized evidence and identified issues.

### 4. TimelineAgent

**Purpose**: Generate chronological timelines and track deadlines.

**Capabilities**:
- `timeline_generation` - Create event timeline
- `deadline_tracking` - Track important deadlines
- `event_extraction` - Extract temporal events
- `urgency_detection` - Flag urgent items (within 7 days)
- `milestone_identification` - Identify key milestones

**Features**:
- Chronological sorting
- Overdue event detection
- Urgent deadline flagging
- Milestone extraction

**Input**:
```python
{
    "events": [
        {
            "id": "evt1",
            "description": "Court hearing",
            "date": "2024-01-15T10:00:00Z",
            "type": "hearing",
            "is_deadline": True
        }
    ]
}
```

**Output**: `TimelineSummary` with events, deadlines, overdue/urgent items, milestones.

### 5. RiskAgent

**Purpose**: Identify and assess risks based on structured data.

**Capabilities**:
- `risk_identification` - Identify risk factors
- `risk_assessment` - Assess risk severity
- `severity_classification` - Classify by severity
- `risk_prioritization` - Prioritize by impact

**Risk Levels**:
- Critical (25 points each)
- High (15 points each)
- Medium (8 points each)
- Low (3 points each)

**Risk Types**:
- Missing Evidence
- Weak Evidence
- Overdue Deadlines
- Approaching Deadlines
- Insufficient Documentation
- Execution Errors

**Input**: Uses `evidence_summary` and `timeline_summary` from ExecutionContext

**Output**: `RiskSummary` with categorized risks and risk score (0-100).

### 6. MemoryAgent

**Purpose**: Interface with memory providers for context management.

**Capabilities**:
- `memory_loading` - Load from memory providers
- `memory_storage` - Store to memory providers
- `context_merging` - Merge contexts for LLMs
- `memory_retrieval` - Retrieve specific memory

**Operations**:
- `load` - Load memory from providers
- `store` - Store memory to providers
- `update` - Update existing memory
- `merge` - Merge context for LLM prompts

**Memory Types**:
- Short-term (execution context)
- Long-term (historical data)
- Conversation (dialogue history)
- Case-specific (case context)

**Input**:
```python
{
    "operation": "load",  # or store, update, merge
    "memory_data": {...}  # for store/update
}
```

**Output**: `MemoryContext` with all memory types.

## Common Interface

All agents inherit from `BaseAgent` and implement:

```python
class SpecializedAgent(BaseAgent):
    @property
    def capabilities(self) -> List[str]:
        """Agent capabilities"""
        
    @property
    def required_tools(self) -> List[str]:
        """Required external tools"""
        
    @property
    def required_memory(self) -> List[str]:
        """Required memory providers"""
        
    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute agent logic"""
        
    async def validate(self, context: ExecutionContext) -> bool:
        """Validate execution context"""
        
    async def health(self) -> Dict[str, Any]:
        """Health check"""
        
    def metadata(self) -> Dict[str, Any]:
        """Agent metadata"""
```

## ExecutionContext

Agents communicate through `ExecutionContext`:

```python
context = ExecutionContext(
    case_id="case-123",
    user_id="user-456",
    domain="legal",
    workflow="case_analysis"
)

# Set input data
context.input_data = {"key": "value"}

# Share data between agents
context.set_shared("evidence_summary", summary)
summary = context.get_shared("evidence_summary")

# Add agent output
context.add_agent_output(agent_id, response)

# Add execution trace
context.add_trace(trace)

# Check for errors
if context.has_errors():
    print(context.errors)
```

## Agent Response

All agents return `AgentResponse`:

```python
{
    "agent_id": "ingest_agent",
    "agent_name": "Document Ingest Agent",
    "status": "completed",  # or failed, pending, etc.
    "output": {
        # Agent-specific output
    },
    "error": None,  # Error message if failed
    "duration_ms": 45.23,
    "metadata": {
        # Additional metadata
    }
}
```

## Agent Registration

Agents are automatically registered on startup:

```python
# app/agents/init.py
def initialize_agents():
    specialized_agents = [
        IngestAgent(),
        RetrievalAgent(),
        EvidenceAgent(),
        TimelineAgent(),
        RiskAgent(),
        MemoryAgent(),
    ]
    
    for agent in specialized_agents:
        agent_factory._agent_instances[agent.agent_id] = agent
        
        metadata = AgentMetadata(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            agent_type=agent.__class__.__name__,
            capabilities=agent.capabilities,
            description=agent.description,
            version=agent.version,
            status=AgentStatus.ACTIVE,
            metadata=agent.metadata(),
        )
        agent_registry.register_agent(metadata)
```

## Agent Discovery

Discover agents by capabilities:

```python
from app.registry.agent_registry import agent_registry

# Find agents with specific capability
agents = agent_registry.discover_agents(
    capabilities=["evidence_analysis"]
)

# Find agents by type
agents = agent_registry.discover_agents(
    agent_type="EvidenceAgent"
)

# Get all active agents
agents = agent_registry.list_agents(status=AgentStatus.ACTIVE)
```

## Usage Examples

### Single Agent Execution

```python
from app.agents.ingest_agent import IngestAgent
from app.agents.context import ExecutionContext

# Create context
context = ExecutionContext(case_id="case-1", domain="legal")

# Set input
context.input_data = {
    "content": "Contract between Acme and John Doe...",
    "title": "Settlement Agreement",
    "type": "contract"
}

# Execute agent
agent = IngestAgent()
response = await agent.execute(context)

# Check result
if response.status == "completed":
    summaries = response.output["document_summaries"]
    print(f"Processed {len(summaries)} documents")
```

### Agent Workflow

```python
# Create context
context = ExecutionContext(case_id="case-1", domain="legal")

# Step 1: Ingest documents
context.input_data = {"documents": [...]}
await IngestAgent().execute(context)

# Step 2: Analyze evidence
context.input_data = {"evidence": [...]}
await EvidenceAgent().execute(context)

# Step 3: Generate timeline
context.input_data = {"events": [...]}
await TimelineAgent().execute(context)

# Step 4: Assess risks
context.input_data = {}
risk_response = await RiskAgent().execute(context)

# Access final result
risk_summary = risk_response.output["risk_summary"]
print(f"Risk Score: {risk_summary['risk_score']}/100")
```

### With Orchestrator

```python
from app.agents.orchestrator import Orchestrator, OrchestratorConfig

# Create orchestrator
config = OrchestratorConfig(
    max_retries=3,
    timeout_seconds=300,
    fail_fast=False
)
orchestrator = Orchestrator(config=config)

# Create context with input
context = ExecutionContext(case_id="case-1", domain="legal")
context.input_data = {
    "documents": [...],
    "evidence": [...],
    "events": [...]
}

# Execute workflow
result = await orchestrator.execute_workflow(context)

# Check results
print(f"Status: {result.status}")
print(f"Agents executed: {len(result.agent_responses)}")
```

## Testing

All agents have comprehensive unit tests:

```bash
# Run all agent tests
pytest tests/test_specialized_agents.py -v

# Run specific agent tests
pytest tests/test_specialized_agents.py::TestIngestAgent -v

# Run with coverage
pytest tests/test_specialized_agents.py --cov=app.agents --cov-report=html
```

Example test:

```python
@pytest.mark.asyncio
async def test_ingest_agent():
    agent = IngestAgent()
    context = ExecutionContext(case_id="test-1", domain="legal")
    
    context.input_data = {
        "content": "Test contract",
        "title": "Test",
        "type": "contract"
    }
    
    response = await agent.execute(context)
    
    assert response.status == AgentExecutionStatus.COMPLETED
    assert response.output["total_documents"] == 1
```

## Error Handling

All agents handle errors gracefully:

```python
try:
    response = await agent.execute(context)
    
    if response.status == AgentExecutionStatus.COMPLETED:
        # Success
        result = response.output
    elif response.status == AgentExecutionStatus.FAILED:
        # Failed with error
        error = response.error
        logger.error(f"Agent failed: {error}")
        
except Exception as e:
    # Unexpected exception
    logger.exception(f"Unexpected error: {e}")
```

## Performance

- **Typical Execution**: < 100ms per agent
- **Memory**: Minimal footprint
- **Async**: 100% async operations
- **Stateless**: No agent-level state
- **Scalable**: Can run in parallel

## Observability

### Logging

All agents use structured logging:

```python
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

logger.info("Agent executed", agent_id=agent.agent_id, duration_ms=duration)
logger.error("Agent failed", agent_id=agent.agent_id, error=str(e))
```

### Metrics

Every response includes execution metrics:

```python
response.duration_ms  # Execution time in milliseconds
response.metadata     # Additional metrics
```

### Health Checks

Check agent health:

```python
health = await agent.health()
# Returns: {"agent_id": "...", "status": "healthy", "version": "1.0.0"}
```

## Best Practices

1. **Always validate input** before execution
2. **Use ExecutionContext** to share state between agents
3. **Check response status** before using output
4. **Handle errors gracefully** with try/except
5. **Use type hints** for better IDE support
6. **Log important events** for observability
7. **Test agents in isolation** before integration
8. **Use shared_context** instead of passing data directly
9. **Keep agents stateless** for better scalability
10. **Document agent capabilities** clearly

## What's NOT in Phase 3

Phase 3 explicitly excludes:

- ❌ LLM integration (Claude, OpenAI, etc.)
- ❌ RAG implementation (ChromaDB, embeddings)
- ❌ Legal reasoning or AI decision-making
- ❌ Recommendation generation
- ❌ Natural language understanding

These features are reserved for **Phase 4 (LLM Integration)** and **Phase 5 (RAG Implementation)**.

## Architecture Principles

### 1. Separation of Concerns
- **Data Preparation** (Phase 3) ← Current
- **AI Reasoning** (Phase 4) ← Next
- **Knowledge Retrieval** (Phase 5) ← Future

### 2. Domain Agnostic
All agents work across:
- Legal
- Healthcare
- Insurance
- Finance
- HR
- Compliance
- Any future domain

### 3. Type Safety
- 100% Pydantic models
- No raw dictionaries
- Compile-time checking
- IDE autocomplete

### 4. Composability
- Agents work independently
- Can be chained in workflows
- No tight coupling
- Shared state via ExecutionContext

## Documentation

- **PHASE3_SUMMARY.md** - Complete implementation summary
- **PHASE3_EXAMPLES.md** - Detailed usage examples
- **PHASE3_QUICK_REFERENCE.md** - Quick reference guide
- **DELIVERY_SUMMARY.txt** - Delivery checklist and metrics

## Verification

Run verification tests:

```bash
# Simple verification
python3 test_phase3_simple.py

# Full verification
./verify-phase3.sh

# Unit tests (requires pytest)
pytest tests/test_specialized_agents.py -v
```

## Next Steps

### Phase 4: LLM Integration
- Integrate Claude/Anthropic API
- Build reasoning agents
- Implement prompt management
- Generate recommendations

### Phase 5: RAG Implementation
- Integrate ChromaDB
- Build embedding pipeline
- Implement semantic search
- Add document retrieval

## Contributing

When adding new agents:

1. Inherit from `BaseAgent`
2. Implement all required methods
3. Use Pydantic for inputs/outputs
4. Add to `init.py` for auto-registration
5. Write comprehensive tests
6. Document capabilities clearly

## Support

For issues or questions:
1. Check agent health: `await agent.health()`
2. Review agent metadata: `agent.metadata()`
3. Check logs for structured error messages
4. Run verification scripts
5. Review documentation

---

**Phase 3 Complete** ✅

All specialized agents are production-ready and tested.
