"""API endpoints for settings.

Implements RULE-BE-016: OpenAPI JSON generation.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db_session_dep
from app.api.v1.schemas.settings import (
    SettingsListResponse,
    SettingsResponse,
    SettingsUpdateMultipleRequest,
    SettingsUpdateRequest,
)
from app.core.logging import get_logger
from app.models.setting import Setting

logger = get_logger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get(
    "",
    response_model=SettingsListResponse,
    status_code=status.HTTP_200_OK,
    summary="設定一覧取得",
    description="システムの設定一覧を取得します。",
)
async def get_settings(
    session: Annotated[AsyncSession, Depends(get_db_session_dep)],
) -> SettingsListResponse:
    """Get all settings.

    Args:
        session: Database session.

    Returns:
        SettingsListResponse with paginated settings.
    """
    # Get all settings
    stmt = select(Setting)
    result = await session.execute(stmt)
    settings = result.scalars().all()

    items = []
    for setting in settings:
        items.append(
            SettingsResponse(
                id=setting.id,
                key=setting.key,
                value=setting.value,
                description=setting.description,
                created_at=setting.created_at.isoformat() if setting.created_at else None,
                updated_at=setting.updated_at.isoformat() if setting.updated_at else None,
            )
        )

    return SettingsListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=len(items),
    )


@router.put(
    "",
    response_model=SettingsListResponse,
    status_code=status.HTTP_200_OK,
    summary="設定一括更新",
    description="複数の設定を一括で更新します。",
)
async def update_settings(
    request: SettingsUpdateMultipleRequest,
    session: Annotated[AsyncSession, Depends(get_db_session_dep)],
) -> SettingsListResponse:
    """Update multiple settings at once.

    Args:
        request: Update request with multiple settings.
        session: Database session.

    Returns:
        SettingsListResponse with updated settings.

    Raises:
        HTTPException: If any setting not found.
    """
    updated_items = []

    for setting_update in request.settings:
        # Find setting by key
        stmt = select(Setting).where(Setting.key == setting_update.key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()

        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting {setting_update.key} not found",
            )

        # Update setting
        setting.value = setting_update.value
        if setting_update.description is not None:
            setting.description = setting_update.description

        updated_items.append(
            SettingsResponse(
                id=setting.id,
                key=setting.key,
                value=setting.value,
                description=setting.description,
                created_at=setting.created_at.isoformat() if setting.created_at else None,
                updated_at=setting.updated_at.isoformat() if setting.updated_at else None,
            )
        )

    await session.commit()

    return SettingsListResponse(
        items=updated_items,
        total=len(updated_items),
        page=1,
        page_size=len(updated_items),
    )


@router.put(
    "/{key}",
    response_model=SettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="設定更新",
    description="指定された設定を更新します。",
)
async def update_setting(
    key: str,
    request: SettingsUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session_dep)],
) -> SettingsResponse:
    """Update a setting.

    Args:
        key: Setting key.
        request: Update request with new value.
        session: Database session.

    Returns:
        SettingsResponse with updated setting.

    Raises:
        HTTPException: If setting not found.
    """
    # Find setting by key
    stmt = select(Setting).where(Setting.key == key)
    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting {key} not found",
        )

    # Update setting
    setting.value = request.value
    setting.description = request.description
    await session.commit()
    await session.refresh(setting)

    return SettingsResponse(
        id=setting.id,
        key=setting.key,
        value=setting.value,
        description=setting.description,
        created_at=setting.created_at.isoformat() if setting.created_at else None,
        updated_at=setting.updated_at.isoformat() if setting.updated_at else None,
    )