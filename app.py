import uvicorn

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from correction import router as correct_router
from augmentation import router as augment_router


templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.include_router(correct_router)
app.include_router(augment_router)


@app.get("/")
@app.post("/")
async def root(request: Request):
    return templates.TemplateResponse("SAGE_root.html", {"request": request})


@app.get('/help')
@app.post('/help')
async def root(request: Request):
    return templates.TemplateResponse("SAGE_help.html", {"request": request})


if __name__ == '__main__':
    uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            # workers=(os.cpu_count() // 2),
        )
