from fastapi import FastAPI, HTTPException, Request, Form, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from database import create_db_and_tables
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, create_engine, Session, select
from models import Deck, Flashcard
import random

arquivo_sqlite = "projeto.db"
url_sqlite = f"sqlite:///{arquivo_sqlite}"

engine = create_engine(url_sqlite)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def initFunction(app: FastAPI):
    # Executado antes da inicialização da API
    create_db_and_tables()
    yield
    # Executado ao encerrar a API

app = FastAPI(lifespan=initFunction)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Carregando apenas a moldura do site (index.html)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Carregando o pedaço com os botões de todos os decks (lista_decks.html)

@app.get("/lista_decks", response_class=HTMLResponse)
def listar_decks(request: Request, tema: str = None, modo: str = "revisar"):
    with Session(engine) as session:
        query = select(Deck)
        if tema:
            query = query.where(Deck.tema.contains(tema))
        todos_decks = session.exec(query).all()
        
        return templates.TemplateResponse(
            "partials/lista_decks.html", 
            {"request": request, "decks": todos_decks, "modo": modo}
        )

# Carrega o Quiz de um deck específico que o usuário escolheu (quiz.html)

# O quiz funciona assim: Um card aleatório do deck é sorteado para que o usuário possa revisar seu significado.

# Depois, o usuário pode continuar clicando em "Próximo" para sortear mais cards e revisar mais.

@app.get("/revisar/{deck_id}", response_class=HTMLResponse)
def iniciar_revisao(request: Request, deck_id: int):
    with Session(engine) as session:
        deck = session.get(Deck, deck_id)
        if not deck.flashcards:
            return "<h2 style='color: orange'>Esse deck está vazio.</h2>"
        card_sorteado = random.choice(deck.flashcards)
        
        return templates.TemplateResponse(
            "partials/quiz.html", 
            {
                "request": request, 
                "card": card_sorteado, 
                "deck_id": deck_id
            }
        )
    
# Formulário de busca geral

@app.get("/form_busca", response_class=HTMLResponse)
def form_busca(request: Request, proximo_passo: str = "revisar"):
    return templates.TemplateResponse(
        "partials/busca.html", 
        {"request": request, "proximo_passo": proximo_passo}
    )

# Exibindo o formulário de novo deck

@app.get("/form_novo_deck", response_class=HTMLResponse)
def form_novo_deck(request: Request):
    return templates.TemplateResponse("partials/novo_deck.html", {"request": request})

# Cadastrando um novo deck no BD
  
@app.post("/salvar_deck", response_class=HTMLResponse)
def salvar_deck(request: Request, tema: str = Form(...), descricao: str = Form(None)):
    with Session(engine) as session:
        novo_deck = Deck(tema=tema, descricao=descricao)
        session.add(novo_deck)
        session.commit()
    
    return f"""
    <div class="mensagem-sucesso">
        <h2>O deck '{tema}' foi adicionado ao banco.</h2>
        <button hx-get="/lista_decks" hx-target="#conteudo">Voltar aos Decks</button>
    </div>
"""

# Exibindo o formulário de edição pré-preenchido

@app.get("/form_editar_deck/{deck_id}", response_class=HTMLResponse)
def form_editar_deck(request: Request, deck_id: int):
    with Session(engine) as session:
        deck = session.get(Deck, deck_id)
        if not deck:
            return "<p>Deck não encontrado!</p>"
        
        return templates.TemplateResponse("partials/editar_deck.html", {"request": request, "deck": deck})
    
# Processando a atualização de deck

@app.put("/atualizar_deck/{deck_id}", response_class=HTMLResponse)
def atualizar_deck(
    request: Request, 
    deck_id: int, 
    tema: str = Form(...), 
    descricao: str = Form(None)
):
    with Session(engine) as session:
        deck_desatualizado = session.get(Deck, deck_id)
        if not tema:
            return "<p style='color: blue;'>O campo 'tema' não pode estar vazio ao atualizar um deck. Escolha um tema para seu deck novo.</p>"

        # Atualiza os campos
        deck_desatualizado.tema = tema
        deck_desatualizado.descricao = descricao

        session.add(deck_desatualizado)
        session.commit()

        return f"""
            <div class="mensagem-sucesso">
                <h2>O deck '{tema}' foi atualizado com sucesso!</h2>
                <button hx-get="/lista_decks" hx-target="#conteudo">Voltar aos Decks</button>
            </div>
        """      

# Exibindo o formulário de adicionar mais flashcards

@app.get("/form_novo_card/{deck_id}", response_class=HTMLResponse)
def exibir_formulario_card(request: Request, deck_id: int):
    return templates.TemplateResponse("partials/novo_flashcard.html", {"request": request, "deck_id": deck_id})

# Cadastrando o flashcard no BD

@app.post("/salvar_card", response_class=HTMLResponse)
def salvar_card_no_banco(
    request: Request,
    deck_id: int = Form(...),
    kanji: str = Form(...),
    traducao: str = Form(...),
    frase: str = Form(...),
    nivel: int = Form(...)
):
    with Session(engine) as session:
        novo_card = Flashcard(
            kanji=kanji, 
            traducao=traducao, 
            frase=frase, 
            nivel=nivel, 
            deck_id=deck_id
        )
        session.add(novo_card)
        session.commit()
    
    return f"""
        <div class="mensagem-sucesso">
            <h2>O card '{kanji}' foi adicionado ao banco.</h2>
            <button hx-get="/lista_decks" hx-target="#conteudo">Voltar aos Decks</button>
        </div>
    """

# Deletando deck (junto com todos os flashcards dentro dele)

@app.delete("/deletar_deck/{deck_id}", response_class=HTMLResponse)
def deletar_deck_e_cards(request: Request, deck_id: int):
    with Session(engine) as session:
        deck = session.get(Deck, deck_id)
        query_cards = select(Flashcard).where(Flashcard.deck_id == deck_id)
        cards_para_deletar = session.exec(query_cards).all()
        for card in cards_para_deletar:
            session.delete(card)
        nome_deck = deck.tema
        session.delete(deck)
        session.commit()    

        return f"""
            <div class="mensagem-sucesso">
                <h2>O deck '{nome_deck}' e seus {len(cards_para_deletar)} cards foram removidos!</h2>
                <button hx-get="/lista_decks" hx-target="#conteudo">Voltar aos Decks</button>
            </div>
        """

# Buscando os flashcards para deletar um deles

@app.get("/preparar_delecao/{deck_id}", response_class=HTMLResponse)
def preparar_delecao(request: Request, deck_id: int):
    with Session(engine) as session:

        # Buscamos os cards do deck para o usuário ver os que já existem
        query = select(Flashcard).where(Flashcard.deck_id == deck_id)
        cards = session.exec(query).all()
        
        return templates.TemplateResponse(
            "partials/deletar_card_busca.html", 
            {"request": request, "cards": cards, "deck_id": deck_id}
        )
    
# Deletando um flashcard pelo ID:

@app.delete("/deletar_flashcard/{flashcard_id}", response_class=HTMLResponse) 
def deletar_flashcard(request: Request, flashcard_id: int):
    with Session(engine) as session:
        flashcard = session.get(Flashcard, flashcard_id)
        kanji_removido = flashcard.kanji
        session.delete(flashcard)
        session.commit()

        return f"""
            <div class="mensagem-sucesso">
                <h2>O card '{kanji_removido}' foi removido com sucesso!</h2>
                <button hx-get="/lista_decks" hx-target="#conteudo">Voltar aos Decks</button>
            </div>
        """

# Isso termina os endpoints necessários pro projeto. Abaixo, eu decidi manter alguns outros

#  Esses endpoints foram usados apenas para testar o BD na fase inicial, por isso não envolvem HTMX

# 1. Criando decks

@app.post("/decks")
def criar_deck(deck: Deck):
    with Session(engine) as session:
        session.add(deck)
        session.commit()
        session.refresh(deck)
        return deck

# 2. Criando flashcards

@app.post("/flashcards")
def criar_flashcard(flashcard: Flashcard):
    with Session(engine) as session:

        deck_existe = session.get(Deck, flashcard.deck_id)
        if not deck_existe:
            raise HTTPException(status_code=404, detail="Esse flashcard não pertence a nenhum deck. Crie um deck para poder povoá-lo com esse flashcard.")
    
        session.add(flashcard)
        session.commit()
        session.refresh(flashcard)
        return flashcard
    
# 3. Mostrando todos os decks criados

@app.get("/decks")
def mostrar_decks():
    with Session(engine) as session:
        todos_decks = session.exec(select(Deck)).all()
        return todos_decks
    
# 4. Mostrando todos os flashcards criados

@app.get("/flashcards")
def mostrar_flashcards():
    with Session(engine) as session:
        todos_flashcards = session.exec(select(Flashcard)).all()
        return todos_flashcards

# 5. Buscando deck por tema

@app.get("/decks/busca")
def buscar_deck_por_tema(tema: str):
    with Session(engine) as session:
        query = select(Deck).where(Deck.tema.contains(tema))
        resultado = session.exec(query).all()

        if not resultado:
            raise HTTPException(status_code=404, detail="Não tem nenhum deck com esse tema!")
        
        return resultado

# 6 . Buscando todos os flashcards de um deck

@app.get("/decks/{deck_id}/flashcards")
def todos_flashcards_do_deck(deck_id: int):
    with Session(engine) as session:
        deck = session.get(Deck, deck_id)
        if not deck:
            raise HTTPException(status_code=404, detail="Deck não encontrado!")
        
        query = select(Flashcard).where(Flashcard.deck_id == deck_id)
        flashcards = session.exec(query).all()

        return {
            "deck": deck.tema,
            "total": len(flashcards),
            "cards": flashcards
        }
    
# 7. Buscando flashcards por nível

@app.get("/flashcards/nivel/{nivel}")
def buscar_flashcard_por_nivel(nivel: int):
    with Session(engine) as session:
        query = select(Flashcard).where(Flashcard.nivel==nivel)
        return session.exec(query).all()

# 8. Buscando flashcards por tradução

@app.get("/flashcards/busca")
def buscar_flashcard_por_traducao(termo: str):
    with Session(engine) as session:
        query = select(Flashcard).where(Flashcard.traducao.contains(termo))
        return session.exec(query).all()
    
# 9. Sorteando um flashcard aleatório de QUALQUER deck

@app.get("/flashcards/sorteio/todos")
def sortear_flashcard_global():
    with Session(engine) as session:
        query = select(Flashcard)
        todos_cards = session.exec(query).all()

        if not todos_cards:
            raise HTTPException(
                status_code=404, 
                detail="O banco de dados está vazio. Cadastre alguns Kanjis primeiro!"
            )
        
        card_sorteado = random.choice(todos_cards)

        return {
            "mensagem": "Hora do quiz! Você sabe o que significa esse kanji?",
            "flashcard": card_sorteado
        }

# 10. Atualizando deck

@app.put("/decks/{deck_id}")
def api_atualizar_deck(deck_id: int, deck_novo: Deck):
    with Session(engine) as session:
        deck_desatualizado = session.get(Deck, deck_id)
        if not deck_desatualizado:
            raise HTTPException(status_code=404, detail="Deck desatualizado não encontrado.")
        
        if not deck_novo.tema:
            raise HTTPException(
                status_code = 404,
                detail="O campo 'tema' não pode estar vazio ao atualizar um deck. Escolha um tema para seu deck novo."
            )
        
        deck_desatualizado.tema = deck_novo.tema
        deck_desatualizado.descricao = deck_novo.descricao

        session.add(deck_desatualizado)
        session.commit()
        session.refresh(deck_desatualizado)

        return {"status": "sucesso", "card_atualizado": deck_desatualizado}
    
# 11. Atualizando flashcard

@app.put("/flashcards/{flashcard_id}")
def atualizar_flashcard(flashcard_id: int, card_novo: Flashcard):
    with Session(engine) as session:
        
        card_desatualizado = session.get(Flashcard, flashcard_id)
        if not card_desatualizado:
            raise HTTPException(status_code=404, detail="Flashcard desatualizado não encontrado.")

        if not card_novo.kanji or not card_novo.traducao or not card_novo.frase or not card_novo.nivel:
            raise HTTPException(
                status_code=400, 
                detail="Os campos 'kanji', 'traducao', 'frase' e 'nível' não podem estar vazios ao atualizar um flashcard."
            )

        card_desatualizado.kanji = card_novo.kanji
        card_desatualizado.traducao = card_novo.traducao
        card_desatualizado.frase = card_novo.frase
        card_desatualizado.nivel = card_novo.nivel
        card_desatualizado.deck_id = card_novo.deck_id

        session.add(card_desatualizado)
        session.commit()
        session.refresh(card_desatualizado)
        
        return {"status": "sucesso", "card_atualizado": card_desatualizado}


