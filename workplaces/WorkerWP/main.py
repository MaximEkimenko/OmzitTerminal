from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title=f"Worker Front")

origins = [
    "http://127.0.0.1:8080",
    "http://192.168.8.30:8000",
    "http://localhost:8000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/worker/{ws_number}", response_class=HTMLResponse)
def worker(request: Request, ws_number: int):
    context = {
        'ws_number': ws_number,
    }
    return templates.TemplateResponse(request=request, name="worker.html", context=context)
