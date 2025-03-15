import io
import pandas as pd

from typing import Optional, Dict
from fastapi import UploadFile, APIRouter, Request, Form, File
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sage.spelling_correction import T5ModelForSpellingCorruption,\
    RuM2M100ModelForSpellingCorrection,  \
    AvailableCorrectors


"""
TODO: add language support
"""


templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/correct", tags=["Correction"])


def __init_models() -> None:
    t5_models = {
        AvailableCorrectors.sage_fredt5_large,
        AvailableCorrectors.sage_fredt5_distilled_95m,
        AvailableCorrectors.sage_mt5_large,
        AvailableCorrectors.fred_large,
        AvailableCorrectors.ent5_large,
    }
    m2m100_models = {
        AvailableCorrectors.sage_m2m100_1B,
        AvailableCorrectors.m2m100_1B,
        AvailableCorrectors.m2m100_418M,
    }


class CorrectionRequest(BaseModel):
    """Request model fot correction"""
    model_name: str
    text: Optional[str] = None
    file: Optional[UploadFile] = None
    keep_original: bool = False


class CorrectionResponse(BaseModel):
    """Response model for correction"""
    corrected_text: str


async def __parse_file(file: UploadFile, sep: str = ",") -> str:
    """Parse the uploaded file and return its content"""
    content = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content), sep=sep)
        return df.to_csv(index=False)

    if file.filename.endswith(".tsv"):
        df = pd.read_csv(io.BytesIO(content), sep="\t")
        return df.to_csv(index=False, sep="\t")

    if file.filename.endswith(".txt"):
        return content.decode("utf-8")

    raise ValueError("Unsupported file format")


def __validate_text(request) -> [bool, Dict]:
    if not request.text and not request.file:
        return False, {"error": "Either text or file must be provided"}
    else:
        return True, {""}


def __validate_model(request) -> [bool, Dict]:
    models = [model.name for model in AvailableCorrectors]
    if request.model_name not in models:
        return False, {"error": "Model is not supported"}
    else:
        return True, {""}


@router.get("/")
async def get_correct_page(request: Request):
    return templates.TemplateResponse("SAGE_correct.html", {"request": request})


@router.post("/", response_model=CorrectionResponse)
async def correct(
    model_name: str = Form(...),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    keep_original: bool = Form(False),  # Отсутствует keep_original
):
    """Correction method"""
    request = CorrectionRequest(
        model_name=model_name,
        text=text,
        file=file,
        keep_original=keep_original,
    )
    status, response = __validate_text(request)
    if not status:
        return response

    status, response = __validate_model(request)
    if not status:
        return response

    if request.file:
        try:
            content = await __parse_file(request.file)
        except ValueError as e:
            return {"error": str(e)}
    else:
        content = request.text

    corrected = f"Corrected ({request.model_name}): {content}"

    if request.keep_original and request.file:
        """
        If keep original file
        """
        if request.file.filename.endswith(".csv") or request.file.filename.endswith(".tsv"):
            df = pd.read_csv(io.StringIO(content))
            df.insert(0, "original", df.iloc[:, 0])
            corrected = df.to_csv(index=False)
        elif request.file.filename.endswith(".txt"):
            corrected = "\n".join([f"{line} {line}" for line in content.split("\n")])

    return CorrectionResponse(corrected_text=corrected)
