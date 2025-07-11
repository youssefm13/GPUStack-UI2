# GPUStack UI Development Guide

## 🚀 Quick Start

### 1. Setup Python Environment

The project requires Python 3.12+. A virtual environment has been created for you.

**Activate the environment:**
```bash
source venv/bin/activate
```

**Or use the convenience script:**
```bash
./activate_env.sh
```

### 2. Install Dependencies

Dependencies are already installed in the virtual environment. If you need to reinstall:

```bash
pip install -r backend/requirements.txt
```

### 3. Run the Backend

**Development mode (with auto-reload):**
```bash
cd backend
uvicorn main:app --reload --port 8001
```

**Production mode:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

### 4. Access the Application

- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Frontend**: http://localhost:8001/app

## 🏗️ Project Structure

```
gpustack-ui-clean/
├── backend/                 # FastAPI backend application
│   ├── api/                # API routes and schemas
│   ├── config/             # Configuration settings
│   ├── database/           # Database models and connection
│   ├── middleware/         # Custom middleware
│   ├── models/             # Data models
│   ├── services/           # Business logic services
│   ├── tests/              # Test files
│   └── utils/              # Utility functions
├── frontend/               # Frontend static files
├── monitoring/             # Monitoring configuration
├── nginx/                  # Nginx configuration
└── venv/                   # Python virtual environment
```

## 🧪 Testing

Run tests from the backend directory:

```bash
cd backend
python -m pytest
```

Run with coverage:
```bash
python -m pytest --cov=.
```

## 🐳 Docker Development

For containerized development:

```bash
docker-compose up --build
```

## 📦 Key Dependencies

### Backend
- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **SQLAlchemy**: Database ORM
- **Pillow/OpenCV**: Image processing
- **pdfplumber/camelot-py**: PDF processing
- **pytesseract**: OCR functionality

### Development Tools
- **pytest**: Testing framework
- **alembic**: Database migrations
- **python-dotenv**: Environment management

## 🔧 Environment Variables

Create a `.env` file in the project root:

```env
ENV=development
JWT_SECRET_KEY=your-secret-key
LOG_LEVEL=debug
GPUSTACK_API_BASE=http://your-api-base
GPUSTACK_API_TOKEN=your-api-token
```

## 🚨 Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're in the virtual environment
   ```bash
   source venv/bin/activate
   ```

2. **Port already in use**: Change the port
   ```bash
   uvicorn main:app --reload --port 8002
   ```

3. **Database issues**: Check database connection in `backend/database/connection.py`

4. **Missing dependencies**: Reinstall requirements
   ```bash
   pip install -r backend/requirements.txt
   ```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🎯 Next Steps

1. Set up your IDE/editor for Python development
2. Configure environment variables
3. Explore the API documentation
4. Run the test suite
5. Start developing!

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `python -m pytest`
4. Submit a pull request 