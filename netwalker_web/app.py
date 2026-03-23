"""
NetWalker Web UI - Main Application

A web-based reporting and visualization interface for NetWalker network discovery data.

Author: Mark Oldham
"""

import sys
import logging
import socket
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from backend.utils.config_manager import ConfigurationManager
from backend.database import DatabaseConnection, DeviceQueries, TopologyQueries, StackQueries, StatsQueries
from backend.api import devices, topology, stacks, reports, stats

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Print banner
hostname = socket.gethostname()
execution_path = os.getcwd()

print("=" * 80)
print(f"Program: {config.APP_NAME}")
print(f"Version: {config.APP_VERSION}")
print(f"Author: {config.APP_AUTHOR}")
print("-" * 80)
print(f"Hostname: {hostname}")
print(f"Execution Path: {execution_path}")
print("=" * 80)
print()

# Initialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Web-based reporting and visualization for NetWalker network discovery data"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load database configuration
try:
    config_manager = ConfigurationManager(config.CONFIG_FILE)
    parsed_config = config_manager.load_configuration()
    db_config = parsed_config.get('database', {})
    
    if not db_config.get('enabled'):
        logger.error("Database is not enabled in configuration")
        raise Exception("Database not enabled")
    
    # Initialize database connection
    db = DatabaseConnection(db_config)
    
    # Test connection
    with db.get_cursor() as cursor:
        cursor.execute("SELECT 1")
        logger.info("Database connection successful")
    
except FileNotFoundError:
    logger.error(f"Configuration file not found: {config.CONFIG_FILE}")
    logger.error("Please copy netwalker.ini from NetWalker project to this directory")
    sys.exit(1)
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    sys.exit(1)

# Initialize query classes
device_queries = DeviceQueries(db)
topology_queries = TopologyQueries(db)
stack_queries = StackQueries(db)
stats_queries = StatsQueries(db)

# Store in app state for access in routes
app.state.db = db
app.state.device_queries = device_queries
app.state.topology_queries = topology_queries
app.state.stack_queries = stack_queries
app.state.stats_queries = stats_queries

# Include API routers
app.include_router(devices.router, prefix="/api", tags=["devices"])
app.include_router(topology.router, prefix="/api", tags=["topology"])
app.include_router(stacks.router, prefix="/api", tags=["stacks"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(stats.router, prefix="/api", tags=["stats"])

# Mount static files
if config.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main page"""
    index_file = config.FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>NetWalker Web UI</title></head>
            <body>
                <h1>NetWalker Web UI</h1>
                <p>Welcome to NetWalker Web UI</p>
                <p><a href="/docs">API Documentation</a></p>
            </body>
        </html>
        """)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "version": config.APP_VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")

# Run application
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    logger.info(f"Server: http://{config.HOST}:{config.PORT}")
    logger.info(f"API Docs: http://{config.HOST}:{config.PORT}/docs")
    
    uvicorn.run(
        "app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
