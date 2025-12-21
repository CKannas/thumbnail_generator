# Logging System Documentation

## Overview

The thumbnail_generator package uses Python's built-in `logging` module with a centralized configuration that supports module-specific loggers. This allows for better tracking, filtering, and debugging of log messages from different modules.

## Architecture

### Logger Hierarchy

The logging system uses a hierarchical logger naming convention:

- **Root Logger**: `thumbnail_generator`
  - **Module Loggers**:
    - `thumbnail_generator.thumbnail_gen`
    - `thumbnail_generator.get_youtube_video_ids`
    - `thumbnail_generator.update_youtube_videos`

### Handlers

#### Console Handler
- **Level**: INFO and above
- **Format**: `%(levelname)-8s - %(message)s`
- **Purpose**: Display important messages to the user in real-time

#### File Handler
- **Level**: All levels (DEBUG and above)
- **Format**: `%(asctime)s - %(name)s - %(levelname)-8s - %(message)s`
- **Location**: `logs/thumbnail_generator.log`
- **Rotation**: Automatic rotation at 10MB with 5 backup files retained
- **Purpose**: Persistent logging for debugging and audit trails

## Usage

### Basic Setup

In your main script, initialize logging once at startup:

```python
from thumbnail_generator.logging_config import setup_logging, get_logger

# Initialize the logging system
setup_logging()

# Get a module-specific logger
logger = get_logger(__name__)

# Start using the logger
logger.info("Application started")
```

### Log Levels

| Level | Use Case | Color/Style |
|-------|----------|------------|
| `DEBUG` | Detailed diagnostic information | - |
| `INFO` | General informational messages | - |
| `WARNING` | Warning messages about potential issues | ⚠️ |
| `ERROR` | Error conditions that should be addressed | ❌ |
| `CRITICAL` | Severe errors that may cause shutdown | 🔴 |

### Log Methods

```python
logger.debug("Detailed diagnostic information")
logger.info("General information message")
logger.warning("Warning about a potential issue")
logger.error("Error occurred during operation")
logger.critical("Critical failure - application may crash")
```

## Log Output Examples

### Console Output
```
INFO     - Logging initialized - Level: INFO, Log dir: D:\working\thumbnail_generator\logs
INFO     - Generated thumbnails:
INFO     - /path/to/thumbnail_part_1.png
WARNING  - No thumbnail found for 'Video Title'
ERROR    - Failed to update thumbnail: Permission denied
```

### File Output
```
2025-12-21 01:06:50 - thumbnail_generator - INFO     - Logging initialized - Level: INFO, Log dir: D:\working\thumbnail_generator\logs
2025-12-21 01:06:50 - thumbnail_generator.thumbnail_gen - INFO     - Test message from thumbnail_gen
2025-12-21 01:06:51 - thumbnail_generator.update_youtube_videos - WARNING  - No thumbnail found for 'Part 5'
2025-12-21 01:06:52 - thumbnail_generator.get_youtube_video_ids - INFO     - Retrieved 50 video IDs
```

## Features

### Module-Specific Logger Names

Each module uses its own logger for better filtering and tracking:

```python
# In thumbnail_gen.py
from .logging_config import get_logger
logger = get_logger(__name__)  # Creates "thumbnail_generator.thumbnail_gen"

# In get_youtube_video_ids.py
from .logging_config import get_logger
logger = get_logger(__name__)  # Creates "thumbnail_generator.get_youtube_video_ids"

# In update_youtube_videos.py
from .logging_config import get_logger
logger = get_logger(__name__)  # Creates "thumbnail_generator.update_youtube_videos"
```

### Automatic Log Rotation

The file handler automatically rotates logs:
- **Rotation Trigger**: When log file reaches 10MB
- **Backup Files**: Keeps up to 5 previous log files
- **Naming**: `thumbnail_generator.log`, `thumbnail_generator.log.1`, `thumbnail_generator.log.2`, etc.

### UTF-8 Encoding

All logs are written with UTF-8 encoding, supporting special characters and emoji.

## Advanced Configuration

### Custom Log Levels

To initialize logging with a different level:

```python
import logging
from thumbnail_generator.logging_config import setup_logging

# Initialize with DEBUG level for more verbose output
setup_logging(log_level=logging.DEBUG)
```

### Custom Log Directory

To specify a custom directory for log files:

```python
from pathlib import Path
from thumbnail_generator.logging_config import setup_logging

# Use a custom logs directory
setup_logging(log_dir=Path("/var/log/thumbnail_generator"))
```

### Custom Log Filename

To use a different log file name:

```python
from thumbnail_generator.logging_config import setup_logging

# Use custom log file name
setup_logging(log_file="custom_logs.log")
```

## Cross-Platform Support

The logging system works seamlessly on:
- ✅ Windows (tested with PowerShell and CMD)
- ✅ Linux/Unix
- ✅ macOS

Log file paths are handled using `pathlib.Path` for platform-independent path operations.

## Troubleshooting

### Logs Not Appearing

1. Ensure `setup_logging()` is called before using any loggers
2. Check that the `logs/` directory has write permissions
3. Verify the log level is appropriate for your messages

### Log File Not Created

1. Check that `logs/` directory exists (created automatically)
2. Verify write permissions in the workspace directory
3. Look for error messages in console output

### Module Name Not Showing in Logs

Make sure you're using `get_logger(__name__)` in each module:

```python
# ✅ Correct - will show module-specific name
logger = get_logger(__name__)

# ❌ Wrong - will show generic name
logger = get_logger()
```

## Best Practices

1. **Always initialize logging at startup**
   ```python
   if __name__ == "__main__":
       setup_logging()
       main()
   ```

2. **Use module-specific loggers**
   ```python
   logger = get_logger(__name__)  # At the top of each module
   ```

3. **Use appropriate log levels**
   - Use `info()` for important workflow messages
   - Use `warning()` for potential issues
   - Use `error()` for failures with proper context

4. **Include context in messages**
   ```python
   # ✅ Good - includes context
   logger.warning(f"No thumbnail found for video '{video_title}'")
   
   # ❌ Poor - lacks context
   logger.warning("No thumbnail found")
   ```

5. **Avoid logging sensitive information**
   ```python
   # ❌ Don't log credentials
   logger.info(f"API key: {api_key}")
   
   # ✅ Log safely
   logger.info("Authenticated with API successfully")
   ```
