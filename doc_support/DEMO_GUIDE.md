# Morpheus 360 Demo Guide
**For Data Manager Meeting**

## 🎯 Demo Objective
Show a working **Customer 360 view** pulling **REAL billing and sales data** from BigQuery in real-time.

---

## 📊 What You'll Demonstrate

### Real Data Integration
- ✅ **Live BigQuery Connection** to `looker-studio-htv.HTVallproductssales.Cleaned_LookerStudioBQ`
- ✅ **10 Top Customers** by MRR (highest: Roberto Dononcourt at $933,400 MRR)
- ✅ **Complete Customer Profiles** with products, services, and revenue data
- ✅ **Real-time Query Performance** (sub-second response times)

---

## 🚀 Quick Start (5 Minutes Before Meeting)

### Step 1: Start Backend API
```bash
cd backend
python main.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

✅ **Verification:** Open http://localhost:8000/docs in browser

---

### Step 2: Start Frontend
Open a **new terminal**:
```bash
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

✅ **Verification:** Open http://localhost:3000 in browser

---

### Step 3: Navigate to Customer 360
In your browser, go to:
```
http://localhost:3000/#/customer/360
```

Or click **"Morpheus 360"** in the left sidebar

---

## 🎬 Demo Script

### Opening (30 seconds)
> "I want to show you Morpheus 360 - our Customer Success Intelligence platform. 
> It's already connected to our BigQuery data and pulling real customer information."

**Action:** Show the dashboard with sidebar navigation

---

### Core Demo (2-3 minutes)

#### 1. Show Real Data Connection
**Point to the header badge:** 
- "DATA_SOURCE: looker-studio-htv"
- "BIGQUERY LIVE" (green indicator)

> "This is pulling data in real-time from our `HTVallproductssales` dataset."

---

#### 2. Demonstrate Customer Profile
**Current View Shows:**
- Customer Name & ID
- Monthly Revenue (MRR)
- Health Score
- Active Products/Services
- Billing Status
- Service History

**Key Talking Point:**
> "Here's Roberto Dononcourt - our highest MRR customer at $933,400 across 1,699 products. 
> All this data is coming directly from BigQuery."

---

#### 3. Show Data Breakdown
**Point to the different sections:**

1. **Profile Card** (left) - Customer details, address, contact info
2. **CNS Score** (center) - Client Net Score with radar chart
3. **Component Breakdown** (right) - Billing, Service, Equipment, Interaction scores

**Key Talking Point:**
> "The platform automatically calculates health scores based on their product count, 
> revenue, and account activity - all derived from our sales data."

---

#### 4. Show Morpheus Recommendations
**Scroll to recommendations panel**

> "The system generates actionable recommendations based on customer behavior patterns."

---

## 📋 Key Customers Available for Demo

| Customer ID | Name | MRR | Products | Why Show Them |
|------------|------|-----|----------|---------------|
| 1000208127 | Roberto Dononcourt | $933,400 | 1,699 | **Highest MRR** - Power user |
| 118703 | Tele Haiti | $649,400 | 34 | Corporate client |
| 1000209609 | Davidson Pierre | $396,500 | 185 | High engagement |

**To switch customers:** Change the ID in the URL:
```
http://localhost:3000/#/customer/360?id=118703
```

---

## 💡 Key Talking Points for Your Manager

### 1. **Data Integration**
✅ "We're already connected to BigQuery"  
✅ "Using the existing `HTVallproductssales.Cleaned_LookerStudioBQ` table"  
✅ "No data duplication - querying live"

### 2. **What's Working Today**
✅ Customer profile aggregation  
✅ Revenue calculation (MRR)  
✅ Product/service history  
✅ Health score computation  
✅ Real-time data refresh

### 3. **What We Need From Data Team**

**Discuss:**
- Access to additional datasets (support tickets, network data, CRM)
- Data quality review (some prices include currency symbols)
- Permission to query other tables (billing history, usage metrics)
- Best practices for query optimization

### 4. **Technical Architecture**
- **Frontend:** React + TypeScript
- **Backend:** Python FastAPI
- **Data Layer:** BigQuery connector with service account
- **Deployment:** Google Cloud Run (already deployed)

---

## 🔍 Live API Test (Optional Advanced Demo)

If your manager is technical, show the raw API:

```bash
curl http://localhost:8000/api/v1/customer/1000208127/360 | jq
```

**Shows:**
- Clean JSON response
- Complete customer data structure
- Real-time query execution

---

## 📸 Screenshots to Capture

Before the meeting, capture these for backup:

1. **Dashboard Overview** - Full Customer 360 view
2. **Data Connection Badge** - Showing "BIGQUERY LIVE"
3. **Customer List** - Top 10 customers by MRR
4. **CNS Breakdown** - Radar chart with scores
5. **API Response** - Raw JSON from curl command

**Save to:** `./doc/evidence-demo-YYYYMMDD.png`

---

## ⚠️ Troubleshooting

### Backend won't start
**Issue:** Missing credentials  
**Fix:** Ensure `backend/temp_creds.json` exists

### Frontend shows empty state
**Issue:** Backend not running  
**Fix:** Start backend first (Step 1)

### "Customer not found" error
**Issue:** Invalid customer ID  
**Fix:** Use one of the verified IDs from the table above

### Data looks wrong
**Issue:** Price format includes currency  
**Fix:** Already fixed in v1.1 - prices are parsed correctly

---

## 🎯 Success Criteria

Your demo is successful if you can show:

✅ **Live Data:** Real customer information from BigQuery  
✅ **Performance:** Page loads in < 2 seconds  
✅ **Accuracy:** MRR and product counts match expectations  
✅ **Professional UI:** Clean, modern interface  
✅ **Scalability:** Can handle multiple customers

---

## 📞 Meeting Questions to Expect

### Q: "How much does this cost to run?"
**A:** "Cloud Run is pay-per-use. Current estimate: ~$50/month for moderate usage. 
BigQuery queries are minimal (~$5/month at current volume)."

### Q: "Can we add more data sources?"
**A:** "Absolutely. The platform is designed to integrate multiple sources. 
Today it's BigQuery, we can add Salesforce, support desk, etc."

### Q: "How real-time is this?"
**A:** "Every page load queries BigQuery directly - it's as real-time as our data warehouse."

### Q: "What about data security?"
**A:** "Using service account with read-only permissions. No data is stored in the app - 
we query on-demand. Can add VPC networking for internal-only access."

### Q: "Can other teams use this?"
**A:** "Yes! Customer Success, Sales, Support can all benefit. We'd build 
role-based access control and custom views per team."

---

## 🔄 Post-Demo Next Steps

After the meeting, you can discuss:

1. **Expand Data Sources**
   - Add support ticket data
   - Integrate network monitoring
   - Connect CRM (Kommo/Salesforce)

2. **Advanced Features**
   - Predictive churn modeling
   - Automated alerts for at-risk customers
   - Customer segmentation
   - Export reports

3. **Team Rollout**
   - Train Customer Success team
   - Create dashboards for Sales
   - Build support desk integration

---

## 📝 Demo Checklist

**30 Minutes Before:**
- [ ] Backend credentials in place (`backend/temp_creds.json`)
- [ ] Test backend starts: `cd backend && python main.py`
- [ ] Test frontend starts: `npm run dev`
- [ ] Verify Customer 360 loads
- [ ] Take backup screenshots

**5 Minutes Before:**
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Browser open to http://localhost:3000/#/customer/360
- [ ] Have customer ID list ready

**During Demo:**
- [ ] Show live data connection
- [ ] Navigate through customer profile
- [ ] Explain data sources
- [ ] Discuss next steps

**After Demo:**
- [ ] Document feedback
- [ ] List requested features
- [ ] Schedule follow-up

---

## 🎉 You're Ready!

This demo shows:
- ✅ Working platform with real data
- ✅ BigQuery integration in action
- ✅ Professional UI and UX
- ✅ Scalable architecture

**Good luck with your meeting!** 🚀

---

**Questions?** Run the test script for verification:
```bash
cd backend && python test_customer360_demo.py
```
