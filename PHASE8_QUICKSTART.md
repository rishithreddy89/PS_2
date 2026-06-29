# Phase 8 Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Backend running on http://localhost:8000
- Frontend running on http://localhost:5173
- MySQL database configured
- OpenAI API key set

### Step 1: Start Services

**Terminal 1 - Backend:**
```bash
cd PS_2
./run-backend.sh
```

**Terminal 2 - Frontend:**
```bash
cd PS_2/frontend
npm run dev
```

### Step 2: Verify Installation
```bash
./verify-phase8.sh
```

### Step 3: Test Complete Workflow

#### A. Upload Documents

1. Open http://localhost:5173
2. Navigate to **Cases**
3. Click on any existing case (or create new one)
4. In Quick Actions, click **Upload Document**
5. Drag & drop files OR click to select:
   - PDF files
   - Word documents (.docx)
   - Text files (.txt)
   - Markdown files (.md)
6. Click **Upload**
7. Watch status change: `processing` → `indexed`

#### B. Generate Analysis

1. Click **Generate Analysis** button
2. Watch the live progress modal:
   - ⏳ Planning workflow...
   - 🤖 Executing agents (Ingest, Retrieval, Evidence, etc.)
   - 📊 Progress bar updates
   - 📝 Live execution logs
3. Wait for completion (~30-60 seconds)
4. See top 3 recommendations appear automatically

#### C. Review Recommendations

1. Click **Request Review** button
2. Review modal shows:
   - Recommendation details
   - Confidence score
   - Supporting evidence
   - Legal basis
3. Select your decision:
   - ✅ **Approve** - Accept recommendation
   - ❌ **Reject** - Decline recommendation
   - ✏️ **Modify** - Suggest changes
4. Add comments (optional)
5. Click **Submit Review**
6. Feedback is stored in memory for future recommendations

## 📋 Quick Test Checklist

- [ ] Backend API responds at http://localhost:8000/health
- [ ] Frontend loads at http://localhost:5173
- [ ] Can create a new case
- [ ] Can upload a document (shows success)
- [ ] Document appears in Documents section
- [ ] Document status becomes "indexed"
- [ ] Can click "Generate Analysis"
- [ ] Progress modal shows live updates
- [ ] Recommendations appear after analysis
- [ ] Can click "Request Review"
- [ ] Review modal displays recommendation details
- [ ] Can submit review (approve/reject/modify)
- [ ] Success message appears

## 🎯 Expected Behavior

### Upload Success
```
✓ File uploaded (2.3 KB)
✓ Processing...
✓ Indexed successfully
```

### Analysis Progress
```
⏳ Planning workflow...
✓ Plan created (9 agents selected)
🤖 Ingest Agent completed (1.2s)
🤖 Retrieval Agent completed (2.1s)
🤖 Evidence Agent completed (3.4s)
...
✅ Analysis complete!
```

### Review Submission
```
✓ Review submitted successfully
✓ Memory updated
```

## 🐛 Troubleshooting

### Document Upload Fails
```bash
# Check uploads directory
ls -la uploads/

# Check logs
tail -f logs/app.log
```

### Analysis Doesn't Start
```bash
# Verify agents registered
curl http://localhost:8000/api/v1/agents

# Check planner
curl http://localhost:8000/api/v1/planner/status
```

### Frontend Connection Issues
```bash
# Check CORS settings
grep CORS_ORIGINS .env

# Verify API URL
grep VITE_API_URL frontend/.env
```

## 📊 Sample Test Data

**Test Case:**
```json
{
  "case_number": "TEST-001",
  "title": "Sample Legal Case",
  "status": "open",
  "priority": "high",
  "case_type": "civil",
  "client_name": "John Doe"
}
```

**Test Document:**
Create `test_doc.txt`:
```
This is a test legal document for LexMind AI.
It contains sample case information for analysis.
The case involves contract dispute between parties.
```

## 🎬 Demo Script

**5-Minute Demo:**

1. "Let me show you LexMind AI's case workflow"
2. Navigate to Cases → Select case
3. "First, we upload legal documents" → Upload demo doc
4. "Documents are automatically parsed and indexed" → Show status
5. "Now let's generate AI analysis" → Click Generate Analysis
6. "Watch the AI workflow execute in real-time" → Show progress
7. "The planner dynamically selects specialized agents"
8. "Each agent contributes to the analysis"
9. "Within 30 seconds, we get top 3 recommendations"
10. "Lawyers can review and provide feedback" → Click Review
11. "This creates a human-in-the-loop system"
12. "Feedback improves future recommendations"

## ✅ Success Indicators

You'll know Phase 8 is working when:

1. ✓ Documents upload without errors
2. ✓ Status changes to "indexed" within 5 seconds
3. ✓ Analysis progress streams live updates
4. ✓ Recommendations generate automatically
5. ✓ Review modal displays full details
6. ✓ Feedback saves successfully
7. ✓ No manual page refresh needed
8. ✓ All actions complete in < 60 seconds

## 🚨 Common Errors

| Error | Solution |
|-------|----------|
| "Connection refused" | Start backend: `./run-backend.sh` |
| "CORS error" | Check CORS_ORIGINS in .env |
| "Upload failed" | Check uploads/ directory permissions |
| "Analysis stuck" | Check OpenAI API key |
| "No recommendations" | Verify NBA agent registered |

## 📞 Need Help?

1. Check logs: `tail -f logs/app.log`
2. Run verification: `./verify-phase8.sh`
3. Review docs: `PHASE8_DOCUMENTATION.md`
4. Test APIs: http://localhost:8000/docs

## 🎉 Next Steps

Once Phase 8 is verified:
- Explore advanced agent configurations
- Customize recommendation thresholds
- Add custom document types
- Integrate with external legal databases
- Deploy to production

---

**Phase 8 Complete! 🚀**

Your LexMind AI platform now has a fully functional end-to-end workflow from document upload to AI analysis to human review.
