from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory=["templates", "templates/partials"])
app.mount("/static", StaticFiles(directory="static"), name="static")

curtidas_atual = {"curtidas": 0}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, "curtidas": curtidas_atual["curtidas"]
    })

@app.post("/curtir")
async def curtir(request: Request):
    curtidas_atual["curtidas"] += 1
    return templates.TemplateResponse("curtidas.html", {
        "request": request, "curtidas": curtidas_atual["curtidas"]
    })

@app.post("/retirar-curtidas")
async def retirar_curtidas(request: Request):
    curtidas_atual["curtidas"] = 0
    return templates.TemplateResponse("curtidas.html", {
        "request": request, 
        "curtidas": curtidas_atual["curtidas"]
    })

@app.get("/aba/{aba_nome}")
async def get_aba(request: Request, aba_nome: str):
    return templates.TemplateResponse(f"{aba_nome}.html", {
        "request": request, 
        "curtidas": curtidas_atual["curtidas"]
    })