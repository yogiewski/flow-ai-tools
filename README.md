# Flow AI Chat - Streamlit Cloud Deployment

This app is designed for deployment on Streamlit Cloud.

## Features
- Single-page Streamlit app with FlowAI as the main interface for LLM chat
- Prompt management system
- Configurable LLM endpoints
- Professional UI for sales teams

## Setup
1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository
5. Set the main file path to `app/FlowAI.py`
6. Add secrets in the Streamlit Cloud dashboard:
   ```
   LLM_BASE_URL = "http://your-llm-server.com"
   LLM_PORT = "1234"
   LLM_API_FLAVOR = "openai-compatible"
   LLM_DEFAULT_MODEL = "your-model"
   ```

## Local Development
```bash
pip install -r requirements.txt
streamlit run app/FlowAI.py
```