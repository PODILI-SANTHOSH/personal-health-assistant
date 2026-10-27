from fastapi import APIRouter

router = APIRouter()


@router.get('/')
def read_root() -> dict:
    return {
        'message': 'Personal Health Assistant API',
        'version': '1.0.0',
        'status': 'ok'
    }


@router.get('/health')
def health_check() -> dict:
    return {'status': 'ok'}
