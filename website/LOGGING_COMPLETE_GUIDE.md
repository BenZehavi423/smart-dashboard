# Complete Logging System Guide

## Table of Contents
1. [Code Explanation](#code-explanation)
2. [Parameter Documentation](#parameter-documentation)
3. [Log Analysis](#log-analysis)
4. [Best Practices](#best-practices)
5. [Usage Example](#usage-example)

## Code Explanation

### Log Types and Details

#### 1. Details in each log
- **Timestamp**: When the log was created
- **Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Module**: Which Python module generated the log (automatic)
- **Function**: Which function generated the log (automatic)
- **Line**: Line number in the source code (automatic)
- **Message**: The actual log message

#### 2. Basic Log Levels

| Level | Color | Usage | Console Output | When to Use |
|-------|-------|-------|----------------|-------------|
| DEBUG | Cyan | Detailed debugging information | Only in debug mode | Development only |
| INFO | Green | General information messages | Always | Application flow |
| WARNING | Yellow | Something unexpected happened but the application can continue | Always | Potential issues |
| ERROR | Red | Something failed but the application can continue | Always | Errors that need attention |
| CRITICAL | Red Background | Application cannot continue | Always | System failures |
| EXCEPTION | Red | Exception with traceback | Always | Debugging exceptions |

#### 3. Specialized Log Methods
```python
# HTTP Request Logging
logger.request("GET", "/api/users", 200, 0.5, "user123")
# Details: method, URL, status_code, duration, user_id

# Database Operation Logging
logger.database("find", "users", 0.1, True)
# Details: operation, collection, duration, success, error

# Authentication Logging
logger.auth("login", "user123", True, "192.168.1.100")
# Details: action, user_id, success, ip_address

# File Upload Logging
logger.file_upload("data.csv", 1024*1024, "user123", True)
# Details: filename, file_size, user_id, success, error
```

#### 4. Structured Logging with Extra Fields
```python
logger.info("User action performed", extra_fields={
    "action_type": "button_click",
    "button_id": "submit_form",
    "page": "profile",
    "session_id": "sess_12345"
})
```

### Integration in Your Code

#### 1. In Flask Views
```python
from web.logger import logger

@app.route('/api/users')
def get_users():
    logger.info("API request received", extra_fields={
        "endpoint": "/api/users",
        "user_id": get_current_user_id()
    })
    
    try:
        users = db.get_users()
        logger.info("Users retrieved successfully", extra_fields={
            "count": len(users)
        })
        return jsonify(users)
    except Exception as e:
        logger.exception("Failed to retrieve users")
        return jsonify({"error": "Internal server error"}), 500
```

#### 2. In Database Operations
```python
from web.logger import logger
import time

def find_user(user_id):
    start_time = time.time()
    try:
        user = db.users.find_one({"_id": user_id})
        duration = time.time() - start_time
        
        logger.database(
            operation="find",
            collection="users",
            duration=duration,
            success=True
        )
        return user
    except Exception as e:
        duration = time.time() - start_time
        logger.database(
            operation="find",
            collection="users",
            duration=duration,
            success=False,
            error=str(e)
        )
        raise
```

#### 3. In Authentication
```python
from web.logger import logger
from flask import request

def login_user(username, password):
    try:
        user = authenticate_user(username, password)
        if user:
            logger.auth(
                action="login",
                user_id=user.id,
                success=True,
                ip=request.remote_addr
            )
            return user
        else:
            logger.auth(
                action="login",
                user_id=username,
                success=False,
                ip=request.remote_addr
            )
            return None
    except Exception as e:
        logger.exception("Login process failed")
        raise
```

## Parameter Documentation

### Basic Log Methods
#### Structure - `logger.<type>(message, extra_fields=None, **kwargs)`
- **message** (str): The log message
- **extra_fields** (dict, optional): Additional context data
- **kwargs**: Additional logging parameters
- **Default values**: None

- **Note**: Exception log automatically includes full traceback

#### Examples:
- `logger.debug("Processing user data", extra_fields={"user_id": "123"})`
- `logger.info("User logged in", extra_fields={"ip": "192.168.1.1"})`
- `logger.warning("High memory usage", extra_fields={"memory": "85%"})`
- `logger.error("Database connection failed", extra_fields={"retry_count": 3})`
- `logger.critical("System shutdown", extra_fields={"reason": "out_of_memory"})`
- `logger.exception("Failed to process request")`

### Specialized Log Methods

#### `logger.request(method, url, status_code, duration, user_id=None)`
- **method** (str): HTTP method (GET, POST, PUT, DELETE, etc.)
- **url** (str): Request URL
- **status_code** (int): HTTP response status code
- **duration** (float): Request duration in seconds
- **user_id** (str, optional): User ID making the request
- **Default values**: user_id=None
- **Log Level**: INFO for status < 400, WARNING for status >= 400
- **Example**: `logger.request("GET", "/api/users", 200, 0.5, "user123")`

#### `logger.database(operation, collection, duration, success, error=None)`
- **operation** (str): Database operation (find, insert, update, delete, aggregate)
- **collection** (str): Collection/table name
- **duration** (float): Operation duration in seconds
- **success** (bool): Whether operation succeeded
- **error** (str, optional): Error message if failed
- **Default values**: error=None
- **Log Level**: INFO for success=True, ERROR for success=False
- **Example**: `logger.database("find", "users", 0.1, True)`

#### `logger.auth(action, user_id=None, success=True, ip=None)`
- **action** (str): Authentication action (login, logout, register, verify)
- **user_id** (str, optional): User ID
- **success** (bool): Whether action succeeded
- **ip** (str, optional): IP address
- **Default values**: user_id=None, success=True, ip=None
- **Log Level**: INFO for success=True, WARNING for success=False
- **Example**: `logger.auth("login", "user123", True, "192.168.1.100")`

#### `logger.file_upload(filename, file_size, user_id, success, error=None)`
- **filename** (str): Name of uploaded file
- **file_size** (int): File size in bytes
- **user_id** (str): User ID uploading the file
- **success** (bool): Whether upload succeeded
- **error** (str, optional): Error message if failed
- **Default values**: error=None
- **Log Level**: INFO for success=True, ERROR for success=False
- **Example**: `logger.file_upload("data.csv", 1024*1024, "user123", True)`

## Log Analysis

### Built-in Analysis Tool

Run the analysis script:
```bash
# Basic analysis
python log_analyzer.py

# Filter by level
python log_analyzer.py --level ERROR

# Filter by module
python log_analyzer.py --module auth

# Search for specific terms
python log_analyzer.py --search "database"

# Filter by time range
python log_analyzer.py --start-time "2024-01-15 10:00:00" --end-time "2024-01-15 11:00:00"

# Export filtered logs
python log_analyzer.py --level ERROR --export errors.json --format json

# Limit results
python log_analyzer.py --limit 100
```

### Free Online Log Analysis Tools

#### A. **Loggly** (Free tier available)
- Upload JSON logs
- Real-time search and filtering
- Dashboard and alerts
- **URL**: https://www.loggly.com/

#### B. **Papertrail** (Free tier available)
- Real-time log aggregation
- Search and filtering
- Mobile app
- **URL**: https://papertrailapp.com/

#### C. **Logentries** (Free tier available)
- Log management and analysis
- Real-time monitoring
- **URL**: https://logentries.com/

#### D. **ELK Stack** (Elasticsearch + Logstash + Kibana)
- Self-hosted solution
- Very powerful but complex
- **URL**: https://www.elastic.co/elk-stack

### 4. Local Analysis Scripts

#### Simple Search Script
```python
#!/usr/bin/env python3
import re
from pathlib import Path

def search_logs(search_term, log_file="website/logs/smart-dashboard.log"):
    with open(log_file, 'r') as f:
        for line in f:
            if search_term.lower() in line.lower():
                print(line.strip())

# Usage
search_logs("error")
search_logs("database")
search_logs("user123")
```

#### Performance Analysis Script
```python
#!/usr/bin/env python3
import re
from collections import defaultdict

def analyze_performance(log_file="website/logs/smart-dashboard.log"):
    request_times = []
    db_times = []
    
    with open(log_file, 'r') as f:
        for line in f:
            # Extract HTTP request times
            match = re.search(r'(\w+) ([^\s]+) - (\d+) \((\d+\.\d+)s\)', line)
            if match:
                method, url, status, duration = match.groups()
                request_times.append(float(duration))
            
            # Extract database operation times
            match = re.search(r'DB (\w+) on (\w+) - (\w+) \((\d+\.\d+)s\)', line)
            if match:
                operation, collection, status, duration = match.groups()
                db_times.append(float(duration))
    
    if request_times:
        print(f"HTTP Requests: {len(request_times)} requests")
        print(f"Average time: {sum(request_times)/len(request_times):.3f}s")
        print(f"Max time: {max(request_times):.3f}s")
    
    if db_times:
        print(f"Database Operations: {len(db_times)} operations")
        print(f"Average time: {sum(db_times)/len(db_times):.3f}s")
        print(f"Max time: {max(db_times):.3f}s")

analyze_performance()
```

### 5. Log File Organization

#### Current Structure
```
website/logs/
├── smart-dashboard.log          # All logs (plain text)
├── smart-dashboard_errors.log   # Errors only (plain text)
├── smart-dashboard_structured.json  # JSON format
├── smart-dashboard.log.1        # Rotated files
├── smart-dashboard.log.2
└── ...
```

## Best Practices

### 1. **When to Use Each Log Level**

#### Use `logger.info()` for:
- Application startup/shutdown
- User actions (login, logout, data access)
- Successful operations
- General application flow

#### Use `logger.error()` for:
- Failed operations that don't crash the app
- Database connection issues
- API call failures
- File processing errors

#### Use `logger.exception()` for:
- Catching exceptions in try/catch blocks
- Debugging issues
- Getting full stack traces

#### Use `logger.warning()` for:
- Deprecated feature usage
- Performance issues
- Security concerns
- Resource usage warnings

#### Use `logger.debug()` for:
- Detailed function execution
- Variable values
- Development-only information

#### Use `logger.critical()` for:
- System failures
- Application crashes
- Security breaches
- Data corruption

### 2. **Specialized vs Basic Logging**

#### Use Specialized Methods When:
- You need consistent formatting
- You want performance metrics
- You plan to analyze logs by operation type
- You want structured data for monitoring

#### Use Basic Methods When:
- You need simple, quick logging
- You don't need the extra context
- You're prototyping or testing

#### Example of Simple Alternative:
```python
# Instead of specialized method
logger.request("GET", "/api/users", 200, 0.5, "user123")

# Use simple logging
logger.info("API request completed", extra_fields={
    "method": "GET", "url": "/api/users", "status": 200, "duration": 0.5
})
```

### 3. **Extra Fields Best Practices**

#### Good Examples:
```python
logger.info("User action", extra_fields={
    "user_id": "123",
    "action": "profile_update",
    "page": "settings"
})

logger.error("API failure", extra_fields={
    "endpoint": "/api/users",
    "status_code": 500,
    "retry_count": 3
})
```

#### Avoid:
```python
# Don't log sensitive data
logger.info("Login attempt", extra_fields={
    "password": "secret123",  # ❌ Never log passwords
    "token": "jwt_token"      # ❌ Never log tokens
})

# Don't log too much data
logger.info("User data", extra_fields={
    "full_user_object": user.__dict__  # ❌ Too verbose
})
```

### 4. **Performance Considerations**

#### Good:
```python
# Log at function entry/exit
def process_user(user_id):
    logger.info("Processing user", extra_fields={"user_id": user_id})
    # ... processing logic ...
    logger.info("User processed successfully")
```

#### Avoid:
```python
# Don't log in tight loops
for i in range(10000):
    logger.debug(f"Processing item {i}")  # ❌ Too many logs
```

### 5. **Error Handling**

#### Good:
```python
try:
    result = risky_operation()
    logger.info("Operation successful")
    return result
except DatabaseError as e:
    logger.error("Database operation failed", extra_fields={"error": str(e)})
    raise
except Exception as e:
    logger.exception("Unexpected error in risky_operation")
    raise
```

## Usage Example

### Simple Usage (Recommended)
```python
from web.logger import logger

# Basic logging
logger.info("User logged in successfully")
logger.error("Database connection failed")
logger.debug("Processing user data")
logger.warning("High memory usage detected")

# With extra context
logger.info("API call completed", extra_fields={
    "endpoint": "/api/users",
    "response_time": 150,
    "user_id": "12345"
})

# Specialized logging
logger.request("GET", "/api/data", 200, 0.5, "user123")
logger.database("find", "users", 0.1, True)
logger.auth("login", "user123", True, "192.168.1.100")
logger.file_upload("data.csv", 1024*1024, "user123", True)
```

### Integration in Your Code
```python
# In any Python file in your project
from web.logger import logger

def some_function():
    logger.info("Starting function execution")
    try:
        # Your code here
        result = process_data()
        logger.info("Function completed successfully")
        return result
    except Exception as e:
        logger.exception("Function failed with error")
        raise
```

## Quick Reference

### Essential Commands
```bash
# Run logging test
python website/test_logging.py

# Analyze logs
python website/log_analyzer.py

# Filter errors only
python website/log_analyzer.py --level ERROR

# Search for specific terms
python website/log_analyzer.py --search "database"
```

### Essential Code Patterns
```python
from web.logger import logger

# Basic logging
logger.info("Operation started")
logger.error("Operation failed")

# Exception logging
try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed")

# With context
logger.info("User action", extra_fields={"user_id": "123"})
```