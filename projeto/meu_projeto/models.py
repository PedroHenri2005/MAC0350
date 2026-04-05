from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


class Deck(SQLModel, table=True):
    decks_id: Optional[int] = Field(default=None, primary_key=True)
    tema: str = Field(index=True, unique=True)
    descricao: Optional[str] = None

    flashcards: List["Flashcard"] = Relationship(back_populates="deck")

class Flashcard(SQLModel, table=True):
    flashcards_id: Optional[int] = Field(default=None, primary_key=True)
    kanji: str = Field(min_length=1)
    traducao: str = Field(min_length=1)
    frase: str = Field(min_length=1)
    nivel: int = Field(ge=1, le=5)

    deck_id: int = Field(foreign_key="deck.decks_id")

    deck: Optional[Deck] = Relationship(back_populates="flashcards")