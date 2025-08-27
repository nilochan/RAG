# 🚀 Deployment Guide - Educational RAG Platform

## 📋 **Quick Deployment Checklist**

### ✅ **What You Have Ready:**
- [x] **GitHub Repository**: https://github.com/nilochan/RAG
- [x] **DeepSeek API Key**: Saved in Railway variables
- [x] **Pinecone API Key**: Saved in Railway variables
- [x] **Code**: Pushed and ready for deployment

---

## 🚂 **Step 1: Deploy Backend on Railway**

### **1.1 Connect GitHub to Railway**
```bash
1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose: nilochan/RAG
5. Select "Deploy Now"
```

### **1.2 Configure Environment Variables in Railway**
**Go to Railway Dashboard → Your Project → Variables → Add Variables:**

```bash
# ✅ DeepSeek AI Configuration
DEEPSEEK_API_KEY = [Your DeepSeek API Key - Already saved]

# ✅ Pinecone Vector Database  
PINECONE_API_KEY = [Your Pinecone API Key - Already saved]
PINECONE_ENVIRONMENT = [Your Pinecone Environment] # e.g., us-west1-gcp
PINECONE_INDEX_NAME = educational-docs

# 📊 Database (Railway will auto-provide)
DATABASE_URL = [Railway PostgreSQL - Auto-generated]

# ⚙️ Application Settings
APP_ENV = production
LOG_LEVEL = INFO
MAX_FILE_SIZE_MB = 10
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CONCURRENT_JOBS = 3
```

### **1.3 Add PostgreSQL Database**
```bash
1. In Railway Dashboard → Add Service
2. Select "PostgreSQL" 
3. Railway will automatically configure DATABASE_URL
```

### **1.4 Your Railway Backend URL**
After deployment, Railway will give you a URL like:
```
https://your-project-name.up.railway.app
```
**📝 Save this URL - you'll need it for Streamlit!**

---

## ☁️ **Step 2: Deploy Frontend on Streamlit Cloud**

### **2.1 Connect GitHub to Streamlit Cloud**
```bash
1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect GitHub account
4. Repository: nilochan/RAG
5. Branch: master
6. Main file path: frontend/app.py
```

### **2.2 Configure Streamlit Secrets**
**In Streamlit Cloud → App Settings → Secrets:**
```toml
API_BASE_URL = "https://your-railway-backend-url.up.railway.app"
```

### **2.3 Your Streamlit App URL**
Streamlit will give you a URL like:
```
https://your-app-name.streamlit.app
```

---

## 🔗 **Step 3: Connect Frontend to Backend**

### **Update API Connection:**
1. **Get your Railway backend URL** (Step 1.4)
2. **Add to Streamlit secrets** (Step 2.2)
3. **Test connection** - Streamlit will show green status if connected

---

## ✅ **Step 4: Verify Everything Works**

### **4.1 Check Backend Health**
```bash
curl https://your-railway-backend-url.up.railway.app/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "components": {
    "database": "operational",
    "pinecone": "operational",
    "deepseek": "operational"
  }
}
```

### **4.2 Test Full Workflow**
1. **Visit your Streamlit app**: https://your-app-name.streamlit.app
2. **Upload a document** (PDF, DOCX, etc.)
3. **Watch real-time progress** (0% → 100%)
4. **Ask a question** about the document
5. **See DeepSeek AI response** with sources

---

## 🎯 **Expected Results**

### **✅ What Should Work:**
- **Document Upload**: Real-time progress tracking
- **AI Responses**: DeepSeek-powered intelligent answers
- **Vector Search**: Pinecone semantic document search
- **Data Persistence**: Documents saved in PostgreSQL
- **Analytics Dashboard**: Live system metrics

### **🚨 Troubleshooting:**

#### **Backend Issues:**
```bash
# Check Railway logs
railway logs

# Test API endpoints
curl https://your-backend-url.railway.app/
```

#### **Frontend Issues:**
```bash
# Check Streamlit logs in dashboard
# Verify API_BASE_URL in secrets
```

#### **DeepSeek API Issues:**
```bash
# Verify API key in Railway variables
# Check API quota: https://platform.deepseek.com/usage
```

#### **Pinecone Issues:**
```bash
# Verify index exists in Pinecone console
# Check environment name matches
```

---

## 💰 **Cost Breakdown**

### **Current Setup:**
- **Streamlit Cloud**: FREE ✅
- **Railway Backend**: $5/month (includes PostgreSQL)
- **DeepSeek API**: Pay-per-use (~$0.002/1K tokens)
- **Pinecone**: Free tier (100K vectors)
- **Total**: ~$5-10/month depending on usage

---

## 🔄 **Future Updates**

### **To Update Your App:**
```bash
# Push changes to GitHub
git add .
git commit -m "Update features"
git push origin master

# Both Railway and Streamlit will auto-deploy! 🚀
```

---

## 📞 **Need Help?**

### **Railway Support:**
- Dashboard: https://railway.app/dashboard
- Logs: Railway Dashboard → Deployments → Logs
- Variables: Railway Dashboard → Variables

### **Streamlit Support:**
- Dashboard: https://share.streamlit.io
- Logs: App Dashboard → Manage app → Logs
- Secrets: App Dashboard → Settings → Secrets

### **API Status:**
- **DeepSeek**: https://platform.deepseek.com
- **Pinecone**: https://app.pinecone.io
- **Your Backend**: https://your-railway-url.railway.app/health

---

## 🎉 **Success! You Should Now Have:**

1. **✅ Backend API** running on Railway with PostgreSQL
2. **✅ Frontend Web App** running on Streamlit Cloud
3. **✅ DeepSeek AI** integration for intelligent responses
4. **✅ Pinecone Vector DB** for document search
5. **✅ Real-time Progress Tracking** for all operations
6. **✅ Analytics Dashboard** with live metrics

**Your RAG platform is now live and ready for users!** 🚀

---

*Last Updated: August 27, 2025*
*Repository: https://github.com/nilochan/RAG*