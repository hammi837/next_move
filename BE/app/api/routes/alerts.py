"""
Alert route module.

CRUD endpoints for user price alerts.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db_session
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate

router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"],
)


@router.get(
    "",
    response_model=list[AlertResponse],
    summary="List user alerts",
)
def list_alerts(
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[AlertResponse]:
    """Return all alerts belonging to the authenticated user."""
    from app.models.alert import Alert

    result = await db.execute(
        select(Alert)
        .where(Alert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
    )
    alerts = result.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alert",
)
def create_alert(
    payload: AlertCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> AlertResponse:
    """Create a new price alert for the authenticated user."""
    from app.models.alert import Alert

    alert = Alert(
        user_id=current_user.id,
        symbol=payload.symbol.upper(),
        condition=payload.condition,
        threshold=payload.threshold,
        is_active=True,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.put(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Update an alert",
)
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> AlertResponse:
    """Update an existing alert owned by the authenticated user."""
    from app.models.alert import Alert

    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id)
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)

    await db.flush()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an alert",
)
def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> None:
    """Delete an alert owned by the authenticated user."""
    from app.models.alert import Alert

    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id)
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    await db.delete(alert)
