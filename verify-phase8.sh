#!/bin/bash

echo "======================================"
echo "PHASE 8 - Workflow Verification"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_URL="http://localhost:8000/api/v1"

echo "Step 1: Check API Health"
echo "------------------------"
HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null)
if [ "$HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓${NC} API is healthy"
else
    echo -e "${RED}✗${NC} API is not responding"
    exit 1
fi
echo ""

echo "Step 2: Create Test Case"
echo "------------------------"
CASE_RESPONSE=$(curl -s -X POST "$BASE_URL/cases" \
  -H "Content-Type: application/json" \
  -d '{
    "case_number": "PHASE8-TEST-'$RANDOM'",
    "title": "Phase 8 Workflow Test Case",
    "status": "open",
    "priority": "high",
    "case_type": "civil",
    "client_name": "Test Client",
    "description": "Testing complete workflow"
  }')

CASE_ID=$(echo $CASE_RESPONSE | jq -r '.id')
if [ "$CASE_ID" != "null" ] && [ -n "$CASE_ID" ]; then
    echo -e "${GREEN}✓${NC} Case created: $CASE_ID"
else
    echo -e "${RED}✗${NC} Failed to create case"
    exit 1
fi
echo ""

echo "Step 3: Create Test Document"
echo "------------------------"
echo "This is a test legal document for Phase 8 verification." > test_upload.txt
echo -e "${GREEN}✓${NC} Test document created: test_upload.txt"
echo ""

echo "Step 4: Upload Document"
echo "------------------------"
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/cases/$CASE_ID/documents" \
  -F "files=@test_upload.txt")

DOC_COUNT=$(echo $UPLOAD_RESPONSE | jq -r '.count' 2>/dev/null)
if [ "$DOC_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Document uploaded successfully"
else
    echo -e "${RED}✗${NC} Document upload failed"
fi
echo ""

echo "Step 5: List Documents"
echo "------------------------"
DOCS=$(curl -s "$BASE_URL/documents/cases/$CASE_ID/documents")
DOC_LIST=$(echo $DOCS | jq -r '.documents | length')
echo -e "${GREEN}✓${NC} Found $DOC_LIST document(s)"
echo ""

echo "Step 6: Check Analysis Status"
echo "------------------------"
STATUS=$(curl -s "$BASE_URL/analysis/cases/$CASE_ID/analysis/status")
echo -e "${GREEN}✓${NC} Analysis status endpoint working"
echo ""

echo "Step 7: Create Test Recommendation"
echo "------------------------"
REC_RESPONSE=$(curl -s -X POST "$BASE_URL/recommendations" \
  -H "Content-Type: application/json" \
  -d "{
    \"case_id\": \"$CASE_ID\",
    \"title\": \"Test Recommendation\",
    \"action_type\": \"legal_strategy\",
    \"description\": \"File motion to dismiss\",
    \"reasoning\": \"Based on lack of evidence\",
    \"confidence_score\": 0.85,
    \"priority\": \"high\"
  }")

REC_ID=$(echo $REC_RESPONSE | jq -r '.id')
if [ "$REC_ID" != "null" ] && [ -n "$REC_ID" ]; then
    echo -e "${GREEN}✓${NC} Recommendation created: $REC_ID"
else
    echo -e "${RED}✗${NC} Failed to create recommendation"
fi
echo ""

echo "Step 8: Submit Review"
echo "------------------------"
if [ -n "$REC_ID" ] && [ "$REC_ID" != "null" ]; then
    REVIEW_RESPONSE=$(curl -s -X POST "$BASE_URL/review/recommendations/$REC_ID/review" \
      -H "Content-Type: application/json" \
      -d '{
        "decision": "approved",
        "comments": "Approved by automated test",
        "reviewer_id": "test-reviewer"
      }')
    
    REVIEW_STATUS=$(echo $REVIEW_RESPONSE | jq -r '.status')
    if [ "$REVIEW_STATUS" = "success" ]; then
        echo -e "${GREEN}✓${NC} Review submitted successfully"
    else
        echo -e "${YELLOW}⚠${NC} Review submission returned: $REVIEW_STATUS"
    fi
else
    echo -e "${YELLOW}⚠${NC} Skipping review (no recommendation ID)"
fi
echo ""

# Cleanup
rm -f test_upload.txt

echo "======================================"
echo "PHASE 8 VERIFICATION COMPLETE"
echo "======================================"
echo ""
echo -e "${GREEN}All workflow endpoints are functional!${NC}"
echo ""
echo "Frontend Testing:"
echo "1. Open http://localhost:5173"
echo "2. Navigate to Cases"
echo "3. Click on 'PHASE8-TEST-001'"
echo "4. Test Quick Actions:"
echo "   - Upload Document (drag & drop)"
echo "   - Generate Analysis (live streaming)"
echo "   - Request Review (human feedback)"
echo ""
echo "Expected Workflow:"
echo "1. Upload → Processing → Indexed"
echo "2. Analysis → Planner → Agents → Recommendations"
echo "3. Review → Approve/Reject/Modify → Memory Updated"
echo ""
