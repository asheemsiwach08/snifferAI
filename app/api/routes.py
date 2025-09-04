from fastapi import APIRouter
from app.api.endpoints import sniffer, scrape_lenders

api_router = APIRouter()

api_router.include_router(sniffer.router)
api_router.include_router(scrape_lenders.router)