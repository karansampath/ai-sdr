# ai-sdr
An AI Sales Development Representative

## Core Features
- **Lead Management**: Complete CRUD operations with automated scoring (0-100 scale)
- **AI-Powered Lead Qualification**: Grok-based intelligent lead assessment with priority assignment
- **Message Personalization**: Multi-variant AI-generated personalized outreach messages
- **Pipeline Management**: Customizable sales pipeline with stage tracking and history
- **Scoring Criteria Management**: Configurable scoring criteria with weighted evaluation
- **Advanced Search**: Full-text search across leads and interactions
- **Meeting Coordination**: Automated meeting scheduling suggestions
- **Evaluation Framework**: Comprehensive testing suite for consistency, performance, and edge cases

## Technical Stack
- **Backend**: FastAPI (Python 3.11+) with async/await support
- **Frontend**: Streamlit web interface
- **Database**: DuckDB for high-performance analytics
- **AI Service**: xAI Grok for lead qualification and message generation
- **Package Management**: uv for fast dependency resolution
- **Linting**: ruff for code quality
- **Templating**: Jinja2 for prompt management
- **Containerization**: Docker support with multi-service orchestration


## Evaluation

Consistency: 50% success rate. Lead qualification shows scoring consistency (78 across 5 trials) but priority assignment inconsistency. Message personalization fully consistent.
Edge Cases: Handled 6 low-priority leads correctly (scores 0-35).
Recommendations: Fix priority assignment logic. Model performs better than expected in failure scenarios.

### Lead Management
Scoring Variations: Three approaches tested (aggressive/conservative/balanced). Enterprise leads consistently high-scored (91-95), startup/mid-level leads vary by approach (45-65).
- Often cases where the startup founder was rated lower than expected

## API Endpoints

**Lead Management**
- `GET /api/leads` - List all leads
- `POST /api/leads` - Create new lead
- `PUT /api/leads/{id}` - Update lead
- `POST /api/leads/{id}/qualify` - Qualify existing lead
- `POST /api/leads/{id}/rescore` - Re-score with custom criteria

**AI Services**
- `POST /api/leads/qualify` - Qualify lead with Grok AI
- `POST /api/messages/personalize` - Generate personalized messages
- `POST /api/leads/{id}/personalize` - Personalize messages for existing lead

**Pipeline Management**
- `GET /api/pipeline/stages` - List pipeline stages
- `POST /api/leads/{id}/pipeline/move` - Move lead to stage
- `GET /api/leads/{id}/pipeline` - Get lead with pipeline history

**Evaluation & Testing**
- `POST /api/evaluate/all` - Run comprehensive evaluation
- `POST /api/evaluate/lead-qualification` - Test lead qualification
- `POST /api/evaluate/message-personalization` - Test message personalization

**Utilities**
- `POST /api/search/leads` - Search leads
- `POST /api/search/interactions` - Search interactions
- `POST /api/leads/{id}/coordinate-meeting` - Schedule meeting
- `GET /health` - Health check

## Deployment Instructions

## Prerequisites
- Python 3.11 or higher
- XAI API key (`XAI_API_KEY` environment variable)
- uv package manager (recommended) or pip

## Method 1: Local Development (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd ai-sdr

# Set up environment
export XAI_API_KEY="your-xai-api-key-here"

# Install dependencies with uv (fast)
uv sync

# Or with pip
pip install -r pyproject.toml

# Run the full application (both FastAPI + Streamlit)
python run.py
```

**Services will be available at:**
- FastAPI Backend: http://localhost:8000
- Streamlit Frontend: http://localhost:8501
- API Documentation: http://localhost:8000/docs

#### Method 2: Docker Deployment
```bash
# Build the container
docker build -t ai-sdr .

# Run with environment variables
docker run -p 8000:8000 -p 8501:8501 \
  -e XAI_API_KEY="your-xai-api-key-here" \
  ai-sdr
```

## Method 3: Individual Services
```bash
# Run FastAPI backend only
python src/main.py

# Run Streamlit frontend only (in separate terminal)
cd frontend
streamlit run streamlit_app.py --server.port=8501
```

#### Production Deployment
For production deployment, consider:
- Use a WSGI server like Gunicorn for FastAPI
- Set up proper logging and monitoring
- Configure environment variables securely
- Use a reverse proxy (nginx) for load balancing
- Set up SSL/TLS certificates

### Troubleshooting Instructions

#### Common Issues

**1. XAI API Key Issues**
```
Error: XAI_API_KEY environment variable not set
```
**Solution:**
- Ensure XAI API key is set: `export XAI_API_KEY="your-key"`
- Verify key validity by testing with Grok demo: `python scripts/grok_demo.py`
- Check key permissions and rate limits

**2. Database Connection Errors**
```
Error: Failed to connect to database
```
**Solution:**
- Ensure `data/` directory exists and is writable
- Check DuckDB version compatibility (`duckdb>=1.3.2`)
- Verify sufficient disk space for database operations

**3. Port Already in Use**
```
Error: [Errno 48] Address already in use
```
**Solution:**
- Kill existing processes: `lsof -ti:8000,8501 | xargs kill`
- Or use different ports in configuration
- Check for other applications using ports 8000/8501

**4. Import/Module Errors**
```
ModuleNotFoundError: No module named 'src'
```
**Solution:**
- Run from project root directory
- Ensure all dependencies installed: `uv sync` or `pip install -r pyproject.toml`
- Check Python path configuration

**5. Streamlit Connection Errors**
```
Error: Cannot connect to FastAPI backend
```
**Solution:**
- Verify FastAPI service is running on port 8000
- Check CORS configuration in `src/main.py`
- Ensure both services started (use `python run.py`)
- Test API directly: `curl http://localhost:8000/health`

**6. Evaluation Test Failures**
```
Evaluation failed: AI service error
```
**Solution:**
- Check XAI API key and quota
- Verify network connectivity
- Run individual tests, eg: `python evaluation_tests/consistency_testing.py`
- Check evaluation results in generated JSON files

## Performance Issues

**Slow Response Times:**
- Check Grok API latency and rate limits
- Monitor database query performance
- Consider implementing caching for frequent requests
- Use async operations where possible

**Memory Usage:**
- Monitor DuckDB memory consumption
- Implement pagination for large datasets
- Clean up old evaluation results periodically

#### Getting Help
1. Check logs in console output
2. Review API documentation at `/docs` endpoint
3. Run the demo script: `python scripts/grok_demo.py`
4. Test individual components using evaluation scripts
5. Verify all environment variables are set correctly

**Log Locations:**
- Application logs: Console output (stdout/stderr)
- Evaluation results: Generated JSON files in evaluation output directory
- Database: DuckDB file in `data/` directory
