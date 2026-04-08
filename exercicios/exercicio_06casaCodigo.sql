-- 1. Definicao dos trabalhos dados
-- Defina: Quais serao as informacoes que sua aplicacao ira manipular? 
-- Voce consegue dizer se existe algum tipo de dado que poderia ser agrupado?

-- RESPOSTA:
-- Basicamente, a minha aplicacao consiste de flashcards, que sao:
-- cartoes onde ficam contidos os ideogramas com traducao, frase, nivel de dificuldade do card, e um ID que aponta pro deck que contem o card, alem do proprio ID do card
-- alem disso, por uma questao de organizacao, flashcards por sua vez serao agrupados em decks, que nada mais sao que um conjunto de flashcards. 
-- decks terao temas(assunto que permeia todos seus flashcards), uma breve descricao do que se trata o deck, e ID.

-- 2. Modelagem do Banco de Dados
-- Defina: Caso haja algum tipo de dado agrupado, existe algum tipo de relacao entre esses grupos?
-- Caso haja relacao, voce consegue dizer quem esta relacionado a quem?
--  Isto eh: dizer quem eh chave primaria e quem eh chave estrangeira?  

-- RESPOSTA:
-- Chaves primarias sao aquelas que identificam o dado de uma maneira unica. Nesse caso, elas sao(ver codigo abaixo):

-- No caso dos decks: decks_id
-- No caso dos flashcards: flashcards_id

-- Chaves estrangeiras sao aquelas que apontam para a chave primaria de uma outra tabela. Observando o codigo abaixo eh facil ver que so tem uma chave desse tipo:

-- No caso dos flashcards: deck_id

-- Como dito anteriormente, cada deck(baralho) pode conter uma quantidade N de flashcards.
-- Contudo, cada flashcard esta contido dentro de apenas um deck atraves do ID que aponta pro deck.
-- Portanto, a relacao aqui eh de Um para Muitos(1:N). Um deck relacionado a N flashcards.

-- Deck
CREATE TABLE deck (
    decks_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tema TEXT NOT NULL UNIQUE,
    descricao TEXT
);

-- Flashcard
CREATE TABLE flashcard (
    flashcards_id INTEGER PRIMARY KEY AUTOINCREMENT,
    kanji TEXT NOT NULL,
    traducao TEXT NOT NULL,
    frase TEXT NOT NULL,
    nivel INTEGER NOT NULL CHECK (nivel >= 1 AND nivel <= 5),
    deck_id INTEGER NOT NULL,
    FOREIGN KEY (deck_id) REFERENCES deck (decks_id)
);
