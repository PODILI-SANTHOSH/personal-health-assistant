from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers.chat import router as chat_router
from backend.routers.documents import router as documents_router
from backend.routers.health import router as health_router
from backend.routers.profile import router as profile_router

app = FastAPI(
    title='Personal Health Assistant',
    version='1.0.0',
    description='Educational health assistant using a retrieval-augmented generation pipeline.'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(profile_router)


@app.get('/api')
def api_info() -> dict:
    return {
        'name': 'Personal Health Assistant API',
        'status': 'running',
        'endpoints': ['/', '/health', '/api/chat', '/api/chat/history', '/api/documents', '/api/profile']
    }
