import time
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from core.config import settings
from repositories.branch_repository import BranchRepository

router = APIRouter(tags=["Frontend Views"])
templates = Jinja2Templates(directory="templates")

# INYECTAR CONFIGURACIONES GLOBALES A TODOS LOS TEMPLATES
templates.env.globals["settings"] = settings
templates.env.globals["cache_buster"] = int(time.time())

@router.get("/instalar", response_class=HTMLResponse)
async def get_instalar(request: Request):
    return templates.TemplateResponse(request=request, name="instalar.html")

@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@router.get("/perfil", response_class=HTMLResponse)
async def get_perfil(request: Request):
    return templates.TemplateResponse(request=request, name="perfil.html")

@router.get("/nuestra-red", response_class=HTMLResponse)
async def get_nuestra_red(request: Request, db: Session = Depends(get_db)):
    branches = BranchRepository.get_all(db)
    return templates.TemplateResponse(request=request, name="nuestra_red.html", context={"branches": branches})

@router.get("/contacto", response_class=HTMLResponse)
async def get_contacto(request: Request):
    return templates.TemplateResponse(request=request, name="contacto.html")

@router.get("/terminos", response_class=HTMLResponse)
async def get_terminos(request: Request):
    return templates.TemplateResponse(request=request, name="terminos.html")

@router.get("/privacidad", response_class=HTMLResponse)
async def get_privacidad(request: Request):
    return templates.TemplateResponse(request=request, name="privacidad.html")

@router.get("/reset-password", response_class=HTMLResponse)
async def get_reset_password(request: Request):
    return templates.TemplateResponse(request=request, name="reset_password.html")

@router.get("/monitoreo", response_class=HTMLResponse)
async def get_monitoreo(request: Request):
    return templates.TemplateResponse(request=request, name="monitoreo_live.html")

@router.get("/estadisticas-ocr", response_class=HTMLResponse)
async def get_estadisticas_ocr(request: Request):
    return templates.TemplateResponse(request=request, name="estadisticas_ocr.html")
