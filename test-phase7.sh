#!/bin/bash

echo "========================================="
echo "LexMind AI - Phase 7 Integration Test"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost:8000"

echo -e "${BLUE}1. Checking backend health...${NC}"
HEALTH=$(curl -s "${BASE_URL}/health")
echo "$HEALTH" | jq '.'

echo ""
echo -e "${BLUE}2. Creating a test case (auto-triggers workflow)...${NC}"
CASE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/cases" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Phase 7 Integration Test Case",
    "case_type": "contract",
    "status": "open",
    "priority": "high",
    "description": "Testing end-to-end workflow integration"
  }')

CASE_ID=$(echo "$CASE_RESPONSE" | jq -r '.id')
EXECUTION_ID=$(echo "$CASE_RESPONSE" | jq -r '.metadata.execution_id // "pending"')
STREAM_URL=$(echo "$CASE_RESPONSE" | jq -r '.metadata.stream_url // ""')

echo "Case created:"
echo "$CASE_RESPONSE" | jq '.'

echo ""
echo -e "${GREEN}✓ Case ID: ${CASE_ID}${NC}"
echo -e "${GREEN}✓ Execution ID: ${EXECUTION_ID}${NC}"
echo -e "${GREEN}✓ Stream URL: ${STREAM_URL}${NC}"

echo ""
echo -e "${BLUE}3. Triggering workflow manually...${NC}"
WORKFLOW_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d "{
    \"case_id\": \"${CASE_ID}\",
    \"workflow_type\": \"full_analysis\"
  }")

echo "$WORKFLOW_RESPONSE" | jq '.'
WORKFLOW_EXEC_ID=$(echo "$WORKFLOW_RESPONSE" | jq -r '.execution_id')

echo ""
echo -e "${BLUE}4. Streaming workflow updates (10 seconds)...${NC}"
echo "Press Ctrl+C to stop streaming"
timeout 10s curl -N "${BASE_URL}${STREAM_URL}" || true

echo ""
echo ""
echo -e "${BLUE}5. Checking workflow metrics...${NC}"
curl -s "${BASE_URL}/api/v1/metrics/workflow" | jq '.'

echo ""
echo -e "${BLUE}6. Checking system metrics...${NC}"
curl -s "${BASE_URL}/api/v1/metrics/system" | jq '.counters, .gauges'

echo ""
echo -e "${BLUE}7. Getting workflow status...${NC}"
if [ "$WORKFLOW_EXEC_ID" != "null" ]; then
  curl -s "${BASE_URL}/api/v1/workflow/status/${WORKFLOW_EXEC_ID}" | jq '.'
fi

echo ""
echo -e "${BLUE}8. Listing all agents...${NC}"
curl -s "${BASE_URL}/api/v1/agents" | jq '[.[] | {agent_id, agent_name, status}]'

echo ""
echo "========================================="
echo -e "${GREEN}✓ Phase 7 Integration Test Complete${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "  - View API docs: ${BASE_URL}/docs"
echo "  - Stream workflow: curl -N ${BASE_URL}${STREAM_URL}"
echo "  - Check metrics: ${BASE_URL}/api/v1/metrics/workflow"
echo ""
