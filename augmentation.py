import asyncio
import uuid

from fastapi import APIRouter, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List

from file_processor import FileProcessor
from corruptor import Corruptor


router = APIRouter(prefix="/augment", tags=["Augmentation"])
templates = Jinja2Templates(directory="templates")

"""
В идеале иметь страницу выбора методов аугментации /augment ?
"""


TASK_RESULTS = {}


class AugmentexRequest(BaseModel):
    """
    Pydantic models can be reused in JS (JSON requests)
    """
    """Request model for Augmentex"""
    level: str = 'word' or 'char'
    language: str = 'ru' or 'en'
    unit_prob: float = 0.0
    min_aug: int = 0
    max_aug: int = 0
    seed: int = 0
    text: Optional[str] = None
    file: Optional[UploadFile] = None


class SBSCRequest(BaseModel):
    """Request model for SBSC"""
    language: str = 'ru' or 'en'
    text: Optional[str] = None
    file: Optional[UploadFile] = None
    dataset: str = None


class PipelineRequest(BaseModel):
    """Request model for Pipeline"""
    # methods: str = None
    method_1: Optional[str] = None
    method_2: Optional[str] = None
    method_3: Optional[str] = None
    language: str = 'ru' or 'en'
    unit_prob: float = 0.0
    min_aug: int = 0
    max_aug: int = 0
    seed: int = 0
    text: Optional[str] = None
    file: Optional[UploadFile] = None
    dataset: str = None


class AugmentResponse(BaseModel):
    """Response model for augmentation"""
    augmented_text: str


@router.get("/augmentex")
async def augment(request: Request):
    return templates.TemplateResponse("SAGE_augmentex.html", {"request": request})


async def start_augmentex_augmentation(task_id: str, content: str, **kwargs):
    corrupt = Corruptor()
    corrupted = await asyncio.to_thread(
        corrupt.corrupt_with_augmentex,
        kwargs['level'],
        kwargs['unit_prob'],
        kwargs['min_aug'],
        kwargs['max_aug'],
        content
    )

    TASK_RESULTS[task_id] = {
        "action": "augmentation",
        "method": "Augmentex",
        "results": [(content, corrupted)],
    }


@router.post("/augmentex")
async def augment_with_augmentex(
        # Добавить mult_num ? (char)
        request: Request,
        level: str = Form(...),
        language: str = Form(...),
        unit_prob: str = Form("0.4"),  # def params from placeholders
        min_aug: str = Form("1"),
        max_aug: str = Form("3"),
        seed: str = Form("77"),
        text: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        background_tasks: BackgroundTasks = BackgroundTasks()
):
    aug_request = AugmentexRequest(
        level=level,
        language=language,
        unit_prob=float(unit_prob),
        min_aug=int(min_aug),
        max_aug=int(max_aug),
        seed=int(seed),
        text=text,
        file=file
    )

    if file and file.filename and file.size > 0:
        content = await FileProcessor.parse_file(file)
    else:
        content = aug_request.text

    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = None

    background_tasks.add_task(start_augmentex_augmentation, task_id, content, **aug_request.dict())
    return RedirectResponse(url=f"/augment/augmentex/wait?task_id={task_id}", status_code=303)


@router.get("/augmentex/wait")
async def wait_for_results(request: Request, task_id: str):
    method = 'augmentex'
    if TASK_RESULTS.get(task_id) is not None:
        return RedirectResponse(url=f"/augment/results/{method}/{task_id}")
    return templates.TemplateResponse("SAGE_augmentex_wait.html",
                                      {"request": request,
                                       "task_id": task_id,
                                       "method": method})


@router.get("/pipeline")
async def augment(request: Request):
    return templates.TemplateResponse("SAGE_pipeline.html", {"request": request})


@router.post("/pipeline")
async def augment_with_pipeline(
        request: Request,
        # methods: List[str] = Form(...),  # Переделать на фронте
        method1: Optional[str] = Form(None),
        method2: Optional[str] = Form(None),
        method3: Optional[str] = Form(None),
        language: str = Form(...),
        unit_prob: float = Form("0.4"),
        min_aug: int = Form("1"),
        max_aug: int = Form("3"),
        seed: int = Form("77"),
        text: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        dataset: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks()
):
    pipe_request = PipelineRequest(
        # methods=methods,
        method_1=method1,
        method_2=method2,
        method_3=method3,
        language=language,
        unit_prob=float(unit_prob),
        min_aug=int(min_aug),
        max_aug=int(max_aug),
        seed=int(seed),
        text=text,
        file=file,
        dataset=dataset
    )

    if file and file.filename and file.size > 0:
        content = await FileProcessor.parse_file(file)
    else:
        content = pipe_request.text

    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = None

    background_tasks.add_task(start_sbsc_augmentation, task_id, language, dataset, content)
    return RedirectResponse(url=f"/augment/sbsc/wait?task_id={task_id}", status_code=303)


@router.get("/sbsc")
async def augment(request: Request):
    return templates.TemplateResponse("SAGE_sbsc.html", {"request": request})


async def start_sbsc_augmentation(task_id: str, content: str, **kwargs):
    corrupt = Corruptor()
    corrupted = await asyncio.to_thread(corrupt.corrupt_with_sbsc, kwargs['language'], kwargs['dataset'], content)

    TASK_RESULTS[task_id] = {
        "action": "augmentation",
        "method": "SBSC",
        "results": [(content, corrupted)],
    }


@router.post("/sbsc")
async def augment_with_sbsc(
        request: Request,
        language: str = Form(...),
        text: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        dataset: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks()
):
    sbsc_request = SBSCRequest(
        language=language,
        text=text,
        file=file,
        dataset=dataset
    )

    if file and file.filename and file.size > 0:
        content = await FileProcessor.parse_file(file)
    else:
        content = sbsc_request.text

    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = None

    background_tasks.add_task(start_sbsc_augmentation, task_id, content, **sbsc_request.dict())
    return RedirectResponse(url=f"/augment/sbsc/wait?task_id={task_id}", status_code=303)


@router.get("/sbsc/wait")
async def wait_for_results(request: Request, task_id: str):
    method = 'sbsc'
    if TASK_RESULTS.get(task_id) is not None:
        return RedirectResponse(url=f"/augment/results/{method}/{task_id}")
    return templates.TemplateResponse("SAGE_sbsc_wait.html",
                                      {"request": request,
                                       "task_id": task_id,
                                       "method": method})


@router.get("/results/{method}/{task_id}")
async def get_results(request: Request, task_id: str, method: str):
    if task_id not in TASK_RESULTS or TASK_RESULTS[task_id] is None:
        return RedirectResponse(url=f"/augment/{method}/wait?task_id={task_id}")
    return templates.TemplateResponse("SAGE_augmentation_results.html",
                                      {"request": request,
                                       **TASK_RESULTS[task_id]})
