# Connection Issues - Root Cause Analysis & Fixes

## Date: January 4, 2026

## Issues Identified

### 1. Dashboard Connection Error
**Symptom**: Dashboard showing "HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded"

**Root Causes**:
1. **Hardcoded localhost**: Dashboard code had `API_BASE_URL = "http://localhost:8000"` which doesn't work inside Docker container
2. **Missing timeout**: API requests had no timeout, causing hanging connections
3. **Poor error handling**: Generic error messages didn't distinguish between timeout vs connection errors

### 2. False "Unhealthy" Status
**Symptom**: `docker compose ps` showed agent-api as "unhealthy"

**Root Cause**: Health check in docker-compose.yml tries to run `curl` command, but curl is not installed in the Python slim container. This is cosmetic - the API was actually working fine.

## Fixes Applied

### Fix 1: Dashboard Connection Configuration
**File**: `/Users/raj/dhcs-intake-lab/dashboard/streamlit_app.py`

**Changes**:
```python
# Before:
API_BASE_URL = "http://localhost:8000"

# After:
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
```

**Impact**: Dashboard now uses the environment variable `API_BASE_URL=http://agent-api:8000` set in docker-compose.yml, enabling proper container-to-container communication.

### Fix 2: Request Timeout and Error Handling
**File**: `/Users/raj/dhcs-intake-lab/dashboard/streamlit_app.py`

**Changes**:
```python
# Before:
def call_api(endpoint: str, data: dict = None, method: str = "POST") -> dict:
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

# After:
def call_api(endpoint: str, data: dict = None, method: str = "POST", timeout: int = 60) -> dict:
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error(f"API request timed out after {timeout} seconds...")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection Error: Unable to reach API at {API_BASE_URL}...")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None
```

**Impact**: 
- 60-second timeout prevents hanging connections
- Clear error messages help diagnose issues
- Graceful handling of different error types

### Fix 3: Uvicorn Server Configuration
**File**: `/Users/raj/dhcs-intake-lab/api/Dockerfile`

**Changes**:
```dockerfile
# Before:
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# After:
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", 
     "--timeout-keep-alive", "75", "--limit-concurrency", "100"]
```

**Impact**:
- `--timeout-keep-alive 75`: Keeps connections alive for 75 seconds to handle long AI queries
- `--limit-concurrency 100`: Allows up to 100 concurrent connections

## Verification Tests

All tests passed after fixes:

### Test 1: Health Check from Dashboard Container
```bash
$ docker exec dashboard python -c "import requests; ..."
Testing connection to: http://agent-api:8000
Status Code: 200
✅ Dashboard can reach API!
```

### Test 2: Full Query Test
```bash
$ docker exec dashboard python -c "import requests; ..."
Testing chat query via: http://agent-api:8000
Status Code: 200
✅ Query successful!
Response: **Query Result:** In the last hour, there have been 4,436 events...
```

### Test 3: External Access
```bash
$ curl http://localhost:8000/health
{"status": "healthy", "timestamp": "2026-01-04T00:07:51.243857"}

$ curl http://localhost:8501
HTTP/1.1 200 OK
✅ Dashboard accessible
```

## Technical Details

### Container Networking
- **Docker Compose Network**: All services are on the same Docker network
- **Service Discovery**: Containers reference each other by service name (e.g., `agent-api`)
- **Port Mapping**: Host ports (8000, 8501) map to container ports for external access

### Connection Flow
```
Browser → localhost:8501 (Dashboard) 
    → agent-api:8000 (FastAPI inside Docker network)
        → OpenAI API (external)
        → pinot-broker:8099 (inside Docker network)
```

## Lessons Learned

1. **Always use environment variables** for configuration in containerized apps
2. **Set timeouts on all network requests** to prevent hanging
3. **Distinguish between different error types** for better debugging
4. **Health checks should use tools available in the container** (or install them)
5. **Container-to-container communication** requires service names, not localhost

## Next Steps

### Immediate
- [x] Dashboard now works correctly
- [x] Connection errors resolved
- [x] Better error messages for debugging

### Optional Improvements
1. Install curl in agent-api container to fix health check
2. Add retry logic for transient failures
3. Implement connection pooling for better performance
4. Add prometheus metrics for monitoring connection health

## Files Modified

1. `/Users/raj/dhcs-intake-lab/dashboard/streamlit_app.py` - Fixed connection and timeout
2. `/Users/raj/dhcs-intake-lab/api/Dockerfile` - Updated uvicorn settings

## System Status

✅ **All connection issues resolved**
✅ **Dashboard → API communication working**
✅ **Proper timeout and error handling implemented**
✅ **System ready for demo**

---

**Verified by**: Claude Code Assistant
**Date**: January 4, 2026
**Containers Rebuilt**: agent-api, dashboard
**Services Restarted**: All services operational
