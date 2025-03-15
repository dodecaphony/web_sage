from typing import Optional

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

router = APIRouter(prefix="/augment", tags=["Augmentation"])
templates = Jinja2Templates(directory="templates")

"""
В идеале иметь страницу выбора методов аугментации /augment ?
"""


class AugmentexRequest(BaseModel):
    """Request model for Augmentex"""
    level: str = 'word' or 'char'
    language: str = 'ru' or 'en'
    unit_prob: float = 0.0
    min_aug: int = 0
    max_aug: int = 0
    seed: int = 0
    text: Optional[str] = None
    file: Optional[UploadFile] = None


class AugmentResponse(BaseModel):
    """Response model for augmentation"""
    augmented_text: str


@router.get("/augmentex")
async def augment(request: Request):
    return templates.TemplateResponse("SAGE_augmentex.html", {"request": request})


@router.post("/augmentex")
async def augment_with_augmentex(
        level: str = Form(...),
        language: str = Form(...),
        unit_prob: str = Form("0.4"),  # def params from placeholders
        min_aug: str = Form("1"),
        max_aug: str = Form("3"),
        seed: str = Form("77"),
        text: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
):
    request = AugmentexRequest(
        level=level,
        language=language,
        unit_prob=unit_prob,
        min_aug=int(min_aug),
        max_aug=int(max_aug),
        seed=int(seed),
        text=text,
        file=file
    )

    augmented_text = (request.text)
    return AugmentResponse(augmented_text=augmented_text)


@router.get("/pipeline")
async def augment_with_pipeline(request: Request):
    return templates.TemplateResponse("SAGE_pipeline.html", {"request": request})


@router.post("/pipeline")
async def augment_with_pipeline(request: Request):
    form_data = await request.form()
    print("Form data:", dict(form_data))
    return templates.TemplateResponse("SAGE_pipeline.html", {"request": request})


@router.get("/sbsc")
async def augment_with_sbsc(request: Request):
    return templates.TemplateResponse("SAGE_sbsc.html", {"request": request})


@router.post("/sbsc")
async def augment_with_sbsc(request: Request):
    form_data = await request.form()
    print("Form data:", dict(form_data))
    return templates.TemplateResponse("SAGE_sbsc.html", {"request": request})
