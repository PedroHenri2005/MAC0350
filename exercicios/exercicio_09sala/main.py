from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, create_engine, Session, select, Field
from typing import Optional
from contextlib import asynccontextmanager

class Aluno(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str

arquivo_sqlite = "alunos.db"
url_sqlite = f"sqlite:///{arquivo_sqlite}"
engine = create_engine(url_sqlite)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def initFunction(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=initFunction)

templates = Jinja2Templates(directory=["templates", "templates/partials"])

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/lista", response_class=HTMLResponse)
def lista(request: Request, busca: str | None = '', pagina: int = 1):
    itens_por_pagina = 10
    inicio = (pagina - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    
    with Session(engine) as session:
        from sqlmodel import col
        query = select(Aluno)
        if busca:
            query = query.where(col(Aluno.nome).contains(busca))
        
        query = query.order_by(Aluno.nome)
        todos_alunos = session.exec(query).all()
        
        alunos = todos_alunos[inicio:fim]
        total_alunos = len(todos_alunos)
        total_paginas = (total_alunos + itens_por_pagina - 1) // itens_por_pagina
    
    return templates.TemplateResponse("lista.html", {
        "request": request,
        "alunos": alunos,
        "pagina": pagina,
        "total_paginas": total_paginas,
        "busca": busca
    })

@app.post("/novoAluno", response_class=HTMLResponse)
def criar_aluno(nome: str = Form(...)):
    with Session(engine) as session:
        novo_aluno = Aluno(nome=nome)
        session.add(novo_aluno)
        session.commit()
        session.refresh(novo_aluno)
        return HTMLResponse(content=f"<p>O(a) aluno(a) {novo_aluno.nome} foi registrado(a)!</p>")

@app.get("/editarAlunos", response_class=HTMLResponse)
def editar_alunos(request: Request):
    return templates.TemplateResponse("options.html", {"request": request})

@app.delete("/apagar", response_class=HTMLResponse)
def apagar():
    return ""