"""
FastAPI Application Entry Point
GLP-1 Drug Label Analysis Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from api.routes import drugs, search, chat, analytics, compare, reports, version_check, watchdog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title="GLP-1 Drug Label Platform API",
    description="AI-powered drug label analysis and search API for GLP-1 medications",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server (primary)
        "http://localhost:3001",  # React dev server (alternate)
        "http://localhost:5173",  # Vite dev server
        # Add production domains here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(drugs.router, prefix="/api/drugs", tags=["Drugs"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(compare.router, prefix="/api/compare", tags=["Comparison"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(version_check.router, prefix="/api/version-check", tags=["Version Check"])


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """API root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "GLP-1 Drug Label Platform API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint"""
    try:
        # TODO: Add database connection check
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2026-01-05T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
