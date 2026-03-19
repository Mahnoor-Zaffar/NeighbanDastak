from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.appointments import router as appointments_router
from app.api.routes.follow_ups import router as follow_ups_router
from app.api.routes.health import router as health_router
from app.api.routes.patients import router as patients_router
from app.api.routes.prescriptions import router as prescriptions_router
from app.api.routes.queue import router as queue_router
from app.api.routes.visits import router as visits_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(analytics_router)
api_router.include_router(patients_router)
api_router.include_router(appointments_router)
api_router.include_router(visits_router)
api_router.include_router(prescriptions_router)
api_router.include_router(queue_router)
api_router.include_router(follow_ups_router)
