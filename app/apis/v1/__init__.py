from fastapi import APIRouter

from app.apis.v1.advice_routers import advice_router
from app.apis.v1.auth_routers import auth_router
from app.apis.v1.challenge_routers import challenge_router
from app.apis.v1.dashboard_routers import dashboard_router
from app.apis.v1.data_export_routers import data_export_router
from app.apis.v1.food_routers import food_router
from app.apis.v1.health_routers import health_router
from app.apis.v1.home_routers import home_router
from app.apis.v1.notification_routers import notification_router
from app.apis.v1.pet_routers import pet_router
from app.apis.v1.prediction_routers import prediction_router
from app.apis.v1.report_routers import report_router
from app.apis.v1.score_routers import score_router
from app.apis.v1.system_routers import system_router
from app.apis.v1.user_routers import policy_router, user_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(auth_router)
v1_routers.include_router(user_router)
v1_routers.include_router(policy_router)
v1_routers.include_router(health_router)
v1_routers.include_router(prediction_router)
v1_routers.include_router(home_router)
v1_routers.include_router(score_router)
v1_routers.include_router(dashboard_router)
v1_routers.include_router(advice_router)
v1_routers.include_router(challenge_router)
v1_routers.include_router(notification_router)
v1_routers.include_router(report_router)
v1_routers.include_router(data_export_router)
v1_routers.include_router(food_router)
v1_routers.include_router(pet_router)
v1_routers.include_router(system_router)
