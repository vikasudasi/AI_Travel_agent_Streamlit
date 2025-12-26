import streamlit as st
import os
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_community.utilities import OpenWeatherMapAPIWrapper, GoogleSerperAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun, YouTubeSearchTool
from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL
from langgraph.graph import MessagesState, StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition

# Page configuration
st.set_page_config(
    page_title="🌍 AI Travel Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Initialize session state
if 'travel_agent' not in st.session_state:
    st.session_state.travel_agent = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'model_provider' not in st.session_state:
    st.session_state.model_provider = "OpenAI"

# Custom Tools
@tool
def addition(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b

@tool
def division(a: int, b: int) -> float:
    """Divide two integers."""
    if b == 0:
        raise ValueError("Denominator cannot be zero.")
    return a / b

@tool
def substraction(a: int, b: int) -> float:
    """Subtract two integers."""
    return a - b

@tool
def get_weather(city: str) -> str:
    """Fetches the current weather of the city from OpenWeatherMap."""
    try:
        weather_api_key = st.secrets.get("OPENWEATHERMAP_API_KEY") or os.getenv("OPENWEATHERMAP_API_KEY")
        if weather_api_key:
            os.environ["OPENWEATHERMAP_API_KEY"] = weather_api_key
            weather = OpenWeatherMapAPIWrapper()
            return weather.run(city)
        else:
            return f"Weather API key not available. Cannot get weather for {city}."
    except Exception as e:
        return f"Weather data unavailable for {city}. Error: {str(e)}"

@tool
def search_google(query: str) -> str:
    """Fetches details about attractions, restaurants, hotels, etc. from Google Serper API."""
    try:
        serper_api_key = st.secrets.get("SERPER_API_KEY") or os.getenv("SERPER_API_KEY")
        if serper_api_key:
            os.environ["SERPER_API_KEY"] = serper_api_key
            search_serper = GoogleSerperAPIWrapper()
            return search_serper.run(query)
        else:
            # Fallback to duck search if serper not available
            return search_duck(query)
    except Exception as e:
        return f"Google search unavailable, trying alternative search. Error: {str(e)}"

@tool
def search_duck(query: str) -> str:
    """Fetches details using DuckDuckGo search."""
    try:
        search_d = DuckDuckGoSearchRun()
        return search_d.invoke(query)
    except Exception as e:
        return f"Search unavailable. Error: {str(e)}"

@tool
def youtube_search(query: str) -> str:
    """Fetches YouTube videos about travel destinations."""
    try:
        youtubetool = YouTubeSearchTool()
        return youtubetool.run(query)
    except Exception as e:
        return f"YouTube search unavailable. Error: {str(e)}"

@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """Get current exchange rate between two currencies using ExchangeRate-API.com.
    
    Args:
        from_currency: Source currency code (e.g., 'INR', 'USD', 'EUR', 'GBP')
        to_currency: Target currency code (e.g., 'USD', 'INR', 'EUR', 'GBP')
    
    Returns:
        str: Current exchange rate and conversion information
    """
    try:
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()
        
        # Get API key from Streamlit secrets or environment
        api_key = st.secrets.get("EXCHANGERATE_API_KEY") or os.getenv("EXCHANGERATE_API_KEY")
        
        if not api_key:
            # Fallback to free API if no key provided
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                if to_currency in rates:
                    rate = rates[to_currency]
                    date = data.get("date", "today")
                    return f"Current exchange rate: 1 {from_currency} = {rate:.4f} {to_currency} (as of {date})"
                else:
                    return f"Currency {to_currency} not found in exchange rates."
            else:
                return f"Unable to fetch exchange rate. Please try again later."
        
        # Use ExchangeRate-API.com v6 with API key
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{from_currency}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("result") == "success":
                conversion_rates = data.get("conversion_rates", {})
                
                if to_currency in conversion_rates:
                    rate = conversion_rates[to_currency]
                    time_last_update = data.get("time_last_update_utc", "recent")
                    
                    # Calculate example conversion
                    example_amount = 100
                    converted_amount = rate * example_amount
                    
                    return f"Current exchange rate: 1 {from_currency} = {rate:.4f} {to_currency} (last updated: {time_last_update}). Example: {example_amount} {from_currency} = {converted_amount:.2f} {to_currency}"
                else:
                    return f"Currency {to_currency} not found. Available currencies include: USD, EUR, GBP, INR, JPY, AUD, CAD, and many more."
            else:
                return f"API returned error: {data.get('error-type', 'Unknown error')}"
        else:
            return f"Unable to fetch exchange rate. Status code: {response.status_code}. Please check your API key."
            
    except requests.exceptions.Timeout:
        return "Request timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        return f"Network error fetching exchange rate: {str(e)}"
    except Exception as e:
        return f"Error fetching exchange rate: {str(e)}. Please try using search_google or search_duck as fallback."

# Advanced calculation tool
python_repl = PythonREPL()
repl_tool = Tool(
    name="python_repl",
    description="A Python shell for complex calculations. Input should be a valid python command.",
    func=python_repl.run,
)

def initialize_travel_agent(model_provider="OpenAI", ollama_base_url="http://localhost:11434"):
    """Initialize the travel agent with all tools and configurations."""
    try:
        # Initialize LLM based on provider
        if model_provider == "Ollama":
            # Check if Ollama is running
            try:
                response = requests.get(f"{ollama_base_url}/api/tags", timeout=2)
                if response.status_code != 200:
                    st.error("❌ Ollama server is not running. Please start Ollama first.")
                    st.info("💡 Run: `ollama serve` in your terminal")
                    return None
            except Exception as e:
                st.error("❌ Cannot connect to Ollama server.")
                st.info(f"💡 Make sure Ollama is running at {ollama_base_url}")
                st.info("💡 Run: `ollama serve` in your terminal")
                return None
            
            # Initialize Ollama model
            llm = ChatOllama(
                model="llama3.2",
                base_url=ollama_base_url,
                temperature=0,
                num_ctx=4096,  # Context window
            )
        else:
            # Get OpenAI API key from Streamlit secrets or environment
            openai_api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
            
            if not openai_api_key:
                st.error("❌ OpenAI API key not found. Please add it to Streamlit secrets.")
                st.info("💡 Go to Settings → Secrets and add: OPENAI_API_KEY = \"your-key-here\"")
                return None
            
            # Initialize OpenAI model
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                max_tokens=2000,
                api_key=openai_api_key
            )
        
        # System prompt
        system_prompt = SystemMessage("""
        You are a professional AI Travel Agent. You MUST follow this EXACT process for every travel query:

        STEP 1: ALWAYS call get_weather tool first for the destination city

        STEP 2: ALWAYS call search_google or search_duck to find:
           - Hotels with specific prices per night
           - Top attractions with entry fees
           - Restaurants with price ranges
           - Transportation options with costs
           
        STEP 2a: CURRENCY CONVERSION: ALWAYS use get_exchange_rate tool first for currency conversions.
           Format: get_exchange_rate("INR", "USD") or get_exchange_rate("USD", "INR")
           This tool provides accurate, real-time exchange rates.
           Only use search_google or search_duck as fallback if the tool fails.

        STEP 3: ALWAYS use arithmetic tools (addition, multiply) to calculate:
           - Hotel cost = daily_rate × number_of_days
           - Total food cost = daily_food_budget × number_of_days
           - Total attraction costs = sum of all entry fees
           - Currency conversion = amount × exchange_rate (from search)
           - Grand total = hotel + food + attractions + transport

        STEP 4: ALWAYS call youtube_search for relevant travel videos

        STEP 5: Create detailed day-by-day itinerary with REAL costs from your searches

        MANDATORY RULES:
        - For currency conversion: SEARCH for current exchange rates, don't guess
        - Use ACTUAL data from tool calls, never make up prices
        - Show detailed cost breakdown with calculations
        - Include weather information from the weather tool
        - Provide YouTube video links from your search

        FORMAT your response as:
        ## 🌤️ Weather Information
        ## 💱 Currency Conversion  
        ## 🏛️ Attractions & Activities
        ## 🏨 Hotels & Accommodation
        ## 📅 Daily Itinerary
        ## 💰 Cost Breakdown
        ## 🎥 YouTube Resources
        ## 📋 Summary
        """)
        
        # Create tools list
        tools = [addition, multiply, division, substraction, get_weather, 
                search_google, search_duck, repl_tool, youtube_search, get_exchange_rate]
        
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(tools)
        
        # Create graph function
        def function_1(state: MessagesState):
            user_question = state["messages"]
            input_question = [system_prompt] + user_question
            response = llm_with_tools.invoke(input_question)
            return {"messages": [response]}
        
        # Build the graph
        builder = StateGraph(MessagesState)
        builder.add_node("llm_decision_step", function_1)
        builder.add_node("tools", ToolNode(tools))
        builder.add_edge(START, "llm_decision_step")
        builder.add_conditional_edges("llm_decision_step", tools_condition)
        builder.add_edge("tools", "llm_decision_step")
        
        # Compile the graph
        react_graph = builder.compile()
        return react_graph
        
    except Exception as e:
        st.error(f"❌ Error initializing travel agent: {str(e)}")
        st.info("💡 Check your API keys and internet connection")
        return None

def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 2rem;'>
        <h1>🌍 AI Travel Agent & Expense Planner</h1>
        <p>Plan your perfect trip with real-time data and detailed cost calculations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Model Provider Selection
    st.sidebar.header("🤖 Model Provider")
    model_provider = st.sidebar.selectbox(
        "Choose AI Model:",
        ["OpenAI", "Ollama"],
        index=0 if st.session_state.model_provider == "OpenAI" else 1,
        key="model_provider_select"
    )
    
    # Update session state if changed
    if model_provider != st.session_state.model_provider:
        st.session_state.model_provider = model_provider
        st.session_state.travel_agent = None  # Reset agent when switching providers
    
    # Ollama configuration (only show if Ollama is selected)
    if model_provider == "Ollama":
        ollama_base_url = st.sidebar.text_input(
            "Ollama Base URL:",
            value="http://localhost:11434",
            help="Default: http://localhost:11434"
        )
        st.session_state.ollama_base_url = ollama_base_url
        
        # Check Ollama connection
        try:
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                st.sidebar.success("✅ Ollama Connected")
                # Check if llama3.2 is available
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if any("llama3.2" in name for name in model_names):
                    st.sidebar.success("✅ llama3.2 Available")
                else:
                    st.sidebar.warning("⚠️ llama3.2 not found")
                    st.sidebar.info("💡 Run: `ollama pull llama3.2`")
            else:
                st.sidebar.error("❌ Ollama Not Running")
        except Exception as e:
            st.sidebar.error("❌ Cannot Connect to Ollama")
            st.sidebar.info("💡 Make sure Ollama is running")
    
    # API Status Check
    st.sidebar.header("📡 API Status")
    
    # Check API keys (only show OpenAI status if OpenAI is selected)
    if model_provider == "OpenAI":
        openai_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if openai_key:
            st.sidebar.success("✅ OpenAI API")
        else:
            st.sidebar.error("❌ OpenAI API Missing")
            st.sidebar.info("Required for OpenAI mode")
    
    serper_key = st.secrets.get("SERPER_API_KEY") or os.getenv("SERPER_API_KEY")
    weather_key = st.secrets.get("OPENWEATHERMAP_API_KEY") or os.getenv("OPENWEATHERMAP_API_KEY")
    
    if serper_key:
        st.sidebar.success("✅ Serper API")
    else:
        st.sidebar.warning("⚠️ Serper API Missing")
        st.sidebar.info("Will use DuckDuckGo as fallback")
        
    if weather_key:
        st.sidebar.success("✅ Weather API")
    else:
        st.sidebar.warning("⚠️ Weather API Missing")
        st.sidebar.info("Weather feature won't work")
    
    # Main content
    st.header("💬 Travel Query")
    
    # Example queries
    example_queries = {
        "🏖️ Beach Vacation": """I want to visit Goa for 5 days in December.
My budget is 30,000 INR.
Get current weather for Goa.
Find hotels under 3,000 INR per night.
I want to know about beaches, water sports, and nightlife.
Calculate exact costs including food (500 INR per day).
Show me travel videos about Goa.""",
        
        "🌍 International Trip": """I want to visit Thailand for 4 days.
My budget is 800 USD.
Convert all costs to Indian Rupees.
Get current weather for Bangkok.
Find budget hotels under 30 USD per night.
Include street food and restaurant costs.
Show temple entry fees and transportation costs.
Calculate total trip cost in both USD and INR."""
    }
    
    selected_example = st.selectbox("🎯 Choose Example Query:", 
                                   ["Custom Query"] + list(example_queries.keys()))
    
    if selected_example != "Custom Query":
        query = st.text_area("✍️ Your Travel Query:", 
                            value=example_queries[selected_example],
                            height=200)
    else:
        query = st.text_area("✍️ Your Travel Query:", 
                            placeholder="E.g., I want to visit Paris for 7 days...",
                            height=200)
    
    # Process button
    if st.button("🚀 Plan My Trip", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter your travel query!")
            return
        
        # Validate provider-specific requirements
        if model_provider == "OpenAI":
            openai_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
            if not openai_key:
                st.error("❌ OpenAI API key is required. Please add it to Streamlit secrets.")
                return
        
        # Initialize travel agent
        if st.session_state.travel_agent is None:
            with st.spinner(f"🔧 Initializing AI Travel Agent with {model_provider}..."):
                ollama_url = st.session_state.get("ollama_base_url", "http://localhost:11434")
                st.session_state.travel_agent = initialize_travel_agent(
                    model_provider=model_provider,
                    ollama_base_url=ollama_url
                )
        
        if st.session_state.travel_agent is None:
            st.error("❌ Failed to initialize travel agent. Please check your API keys.")
            return
        
        # Process the query
        with st.spinner("🤖 Planning your perfect trip..."):
            try:
                response = st.session_state.travel_agent.invoke({
                    "messages": [HumanMessage(query)]
                })
                
                # Display the response
                if response and "messages" in response:
                    final_response = response["messages"][-1].content
                    st.success("✅ Your travel plan is ready!")
                    st.markdown(final_response)
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "query": query,
                        "response": final_response
                    })
                else:
                    st.error("❌ No response received. Please try again.")
                    
            except Exception as e:
                st.error(f"❌ Error processing your request: {str(e)}")
                st.info("💡 Try refreshing the page or check your internet connection")

if __name__ == "__main__":
    main()
