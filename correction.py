import asyncio
import uuid

from fastapi import UploadFile, APIRouter, Request, Form, File, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from file_processor import FileProcessor
from corrector import Corrector
from typing import Optional, Dict


"""
TODO: add language support
"""


router = APIRouter(prefix="/correct", tags=["Correction"])
templates = Jinja2Templates(directory="templates")

TASK_RESULTS = {}


class CorrectionRequest(BaseModel):
    """Request model fot correction"""
    model_name: str = None
    text: Optional[str] = None
    file: Optional[UploadFile] = None


class CorrectionResponse(BaseModel):
    """Response model for correction"""
    corrected_text: str


def __validate_text(request) -> [bool, Dict]:
    if not request.text and not request.file:
        return False, {"error": "Either text or file must be provided"}
    else:
        return True, {""}


@router.get("/")
async def get_correct_page(request: Request):
    return templates.TemplateResponse("SAGE_correct.html", {"request": request})


async def start_correction(task_id: str, model_name: str, batches: list):
    corrector = Corrector()
    corrected = await asyncio.to_thread(corrector.correct, model_name, batches)

    TASK_RESULTS[task_id] = {
        "action": "correction",
        "model": model_name,
        "results": list(zip(batches, corrected))
    }


@router.post("/")
async def correct(
        request: Request,
        model_name: str = Form(...),
        text: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        background_tasks: BackgroundTasks = BackgroundTasks()
):
    corr_request = CorrectionRequest(
        model_name=model_name,
        text=text,
        file=file,
    )

    status, response = __validate_text(corr_request)
    if not status:
        return response

    if file and file.filename and file.size > 0:
        batches = await FileProcessor.parse_file(file)
    else:
        batches = [corr_request.text]

    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = None

    background_tasks.add_task(start_correction, task_id, model_name, batches)
    return RedirectResponse(url=f"/correct/wait?task_id={task_id}", status_code=303)


@router.get("/wait")
async def wait_for_results(request: Request, task_id: str):
    if TASK_RESULTS.get(task_id) is not None:
        return RedirectResponse(url=f"/correct/results/{task_id}")
    return templates.TemplateResponse("SAGE_wait.html", {"request": request, "task_id": task_id})


@router.get("/results/{task_id}")
async def get_results(request: Request, task_id: str):
    if task_id not in TASK_RESULTS or TASK_RESULTS[task_id] is None:
        return RedirectResponse(url=f"/correct/wait?task_id={task_id}")
    return templates.TemplateResponse("SAGE_correction_results.html",
                                      {"request": request,
                                       **TASK_RESULTS[task_id]})

