# Flow AI Chat - Deployment Guide

## 🚀 Quick Deploy

Once Docker is installed, run:

```bash
./deploy.sh
```

This will:
- ✅ Build the Docker container
- ✅ Create configuration files
- ✅ Start the application at http://localhost:8501

## 📋 Manual Deployment

If you prefer manual steps:

```bash
# 1. Build and run with Docker Compose
docker-compose up --build

# 2. Or use newer Docker Compose syntax
docker compose up --build
```

## ⚙️ Configuration

Edit `.env.local` to configure your LLM:

```env
LLM_BASE_URL=http://192.168.1.23  # Your LLM server IP
LLM_PORT=1234                     # Your LLM server port
LLM_API_FLAVOR=openai-compatible  # openai-compatible, ollama, or lmstudio
LLM_DEFAULT_MODEL=gemma-2b        # Your model name
FLOWHUB_HOOKS_ENABLED=false       # Enable for FlowHub integration
```

## 🧪 Testing the App

1. **Access the app** at http://localhost:8501
2. **Configure LLM** in Settings page with your server details
3. **Create prompts** in Prompts Manager
4. **Start chatting** with your private LLM!

## 📁 App Structure

- **Chat Page**: Main interface for LLM conversations
- **Prompts Manager**: Create/edit/manage conversation starters
- **Settings**: Configure LLM endpoints and preferences

## 🔧 Troubleshooting

**Container won't start:**
```bash
docker-compose logs
```

**Permission issues:**
```bash
chmod +x deploy.sh
```

**Port conflicts:**
- Change port in docker-compose.yml if 8501 is busy

## 🌐 Production Deployment

For production, consider:
- Using a reverse proxy (nginx)
- Setting up SSL certificates
- Configuring proper environment variables
- Adding authentication if needed

---

**Ready to test!** 🎉