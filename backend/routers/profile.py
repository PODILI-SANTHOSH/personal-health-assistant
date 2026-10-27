from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.database.store import store
from backend.models.profile import ProfileUpdate

router = APIRouter()


def get_current_user_id() -> str:
    import os
    user_id = os.getenv('CHAT_USER_ID', 'demo-user')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required.')
    return user_id


@router.get('/api/profile')
def get_profile() -> dict:
    user_id = get_current_user_id()
    profile = store.get_or_create_profile(user_id)
    return profile


@router.put('/api/profile')
def update_profile(payload: ProfileUpdate) -> dict:
    user_id = get_current_user_id()
    updated = store.update_profile(user_id, payload.model_dump(exclude_none=True))
    return updated
