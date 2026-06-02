from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models
from core.database import get_db

router = APIRouter(tags=["Frontend Views"])
templates = Jinja2Templates(directory="templates")

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
    branches = db.query(models.ParkingBranch).all()
    return templates.TemplateResponse(request=request, name="nuestra-red.html", context={"branches": branches})

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
