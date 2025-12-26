# 🚀 Streamlit Travel Agent Setup Guide

## 📁 Project Structure (Updated)

```
ai-travel-agent/
├── app.py                    # 🆕 Main Streamlit application
├── Assignment.ipynb          # Original Jupyter notebook  
├── README.md                 # Project documentation
├── requirements.txt          # 🔄 Updated dependencies (includes Streamlit)
├── .env                     # Environment variables (keep local)
├── .gitignore               # Git ignore file
└── .streamlit/              # 🆕 Streamlit configuration (optional)
    └── config.toml          # Custom Streamlit settings
```

## 🔧 Setup Instructions

### 1. **Create the Streamlit App File**

Create `app.py` in your project folder and copy the code from the artifact above.

### 2. **Update Requirements**

Replace your `requirements.txt` with the updated version that includes Streamlit.

### 3. **Verify Your .env File**

Make sure your `.env` file contains:
```env
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here  
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key_here
EXCHANGERATE_API_KEY=your_exchangerate_api_key_here
```

**Note:** 
- If you're using Ollama (local), you don't need the `OPENAI_API_KEY`.
- `EXCHANGERATE_API_KEY` is optional - the app will use a free API if not provided, but having an API key provides better rate limits and features.

### 4. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 5. **Ollama Setup (Optional - for Local AI Model)**

If you want to use local Ollama with `llama3.2` instead of OpenAI:

1. **Install Ollama:**
   - Visit [https://ollama.ai](https://ollama.ai) and download Ollama for your OS
   - Or use: `curl -fsSL https://ollama.com/install.sh | sh`

2. **Start Ollama Server:**
   ```bash
   ollama serve
   ```
   (Keep this running in a separate terminal)

3. **Pull the llama3.2 Model:**
   ```bash
   ollama pull llama3.2
   ```

4. **Verify Installation:**
   ```bash
   ollama list
   ```
   You should see `llama3.2` in the list.

5. **In the Streamlit App:**
   - Select "Ollama" from the "Model Provider" dropdown in the sidebar
   - The app will automatically connect to `http://localhost:11434`
   - If your Ollama server is on a different URL, you can change it in the sidebar

### 6. **ExchangeRate API Key (Optional - for Better Currency Conversion)**

The app includes a dedicated exchange rate tool that works without an API key (uses free API), but you can get better rate limits with an API key:

1. **Get Free API Key:**
   - Visit [ExchangeRate-API.com](https://www.exchangerate-api.com/)
   - Sign up for a free account
   - Get your API key from the dashboard
   - Free tier: 1,500 requests/month

2. **Add to `.env` file:**
   ```env
   EXCHANGERATE_API_KEY=your_api_key_here
   ```

3. **Note:** The exchange rate tool works without an API key, but having one provides:
   - Higher rate limits
   - More reliable service
   - Access to historical data (if needed)

## 🚀 Running Locally

### **Prerequisites:**
- If using **OpenAI**: Make sure your `OPENAI_API_KEY` is set in `.env` or Streamlit secrets
- If using **Ollama**: Make sure Ollama is running (`ollama serve`) and `llama3.2` is pulled

### **Method 1: Simple Run**
```bash
streamlit run streamlit_app.py
```

### **Method 2: Custom Port**
```bash
streamlit run streamlit_app.py --server.port 8080
```

### **Method 3: Development Mode**
```bash
streamlit run streamlit_app.py --server.runOnSave true
```

Your app will open automatically in your browser at `http://localhost:8501`

## 🌐 Deployment Options

### **Option 1: Streamlit Community Cloud (FREE & RECOMMENDED)**

1. **Push to GitHub** (make sure your code is on GitHub)
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Connect your GitHub account**
4. **Deploy your repository:**
   - Repository: `your-username/ai-travel-agent`
   - Branch: `main`
   - Main file path: `app.py`
5. **Add secrets** in Streamlit Cloud dashboard:
   - Go to "Manage app" → "Secrets"
   - Add your API keys:
   ```toml
   OPENAI_API_KEY = "your_key_here"
   SERPER_API_KEY = "your_key_here"  
   OPENWEATHERMAP_API_KEY = "your_key_here"
   ```

**Your app will be live at:** `https://your-app-name.streamlit.app`

### **Option 2: Heroku**

1. **Create `Procfile`:**
```
web: sh setup.sh && streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

2. **Create `setup.sh`:**
```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

3. **Deploy to Heroku:**
```bash
heroku create your-travel-agent-app
git push heroku main
heroku config:set OPENAI_API_KEY=your_key_here
heroku config:set SERPER_API_KEY=your_key_here
heroku config:set OPENWEATHERMAP_API_KEY=your_key_here
```

### **Option 3: Railway**

1. **Connect your GitHub repository**
2. **Add environment variables** in Railway dashboard
3. **Deploy automatically**

## 🎨 Optional: Custom Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
runOnSave = true
```

## 🧪 Testing Your App

### **Test Locally:**
1. Run `streamlit run app.py`
2. Try different example queries
3. Verify all tools are working

### **Test Features:**
- ✅ Weather information displays
- ✅ Search results appear
- ✅ Calculations work correctly
- ✅ YouTube videos load
- ✅ Currency conversion functions
- ✅ Cost breakdown is accurate

## 📱 Mobile Responsiveness

Your Streamlit app is automatically mobile-responsive! Users can access it on:
- 💻 Desktop computers
- 📱 Mobile phones  
- 📟 Tablets

## 🔒 Security Best Practices

### **For Production:**
1. **Never commit API keys** to GitHub
2. **Use Streamlit Secrets** for deployment
3. **Add rate limiting** if needed
4. **Monitor API usage** to avoid overages

### **Environment Variables:**
```python
# In app.py - already handled
import os
from dotenv import load_dotenv
load_dotenv()

# API keys loaded securely
openai_key = os.getenv("OPENAI_API_KEY")
```

## 🐛 Troubleshooting

### **Common Issues:**

**"ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

**"API Key Error"**
- Check your `.env` file
- Verify API keys are correct
- Ensure no extra spaces in API keys

**"Streamlit Command Not Found"**
```bash
pip install streamlit
```

**"Port Already in Use"**
```bash
streamlit run streamlit_app.py --server.port 8502
```

**"Ollama Connection Error"**
- Make sure Ollama is running: `ollama serve`
- Check if the model is installed: `ollama list`
- Pull the model if missing: `ollama pull llama3.2`
- Verify Ollama is accessible: `curl http://localhost:11434/api/tags`
- If using a different port, update the "Ollama Base URL" in the sidebar

## 📈 Performance Tips

1. **Cache API calls** using `@st.cache_data`
2. **Use session state** for expensive operations
3. **Optimize large responses** with pagination
4. **Add loading indicators** for better UX

## 🎯 Next Steps

1. **✅ Create the Streamlit app**
2. **✅ Test locally**  
3. **✅ Deploy to Streamlit Cloud**
4. **✅ Share your live app link!**

## 🌟 Features in Your Streamlit App

- **🎨 Beautiful UI** with custom styling
- **📱 Mobile responsive** design
- **🔄 Real-time processing** with loading indicators
- **📊 Interactive components** (selectboxes, buttons, metrics)
- **💾 Session state** for chat history
- **🎯 Example queries** for easy testing
- **📈 API status monitoring**
- **🎥 Embedded YouTube videos**
- **🤖 Multiple AI Providers** - Switch between OpenAI and local Ollama
- **🔌 Ollama Integration** - Run with local llama3.2 model (no API costs!)

---

**Your travel agent is now a full-featured web application! 🎉**

**Live Demo:** `https://your-app-name.streamlit.app` (after deployment)

