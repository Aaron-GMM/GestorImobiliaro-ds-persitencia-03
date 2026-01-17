# 🏢 Gestor Imobiliário - API NoSQL (MongoDB)

Este projeto é a evolução do sistema de gestão imobiliária, migrado de SQL para um banco de dados orientado a documentos (**MongoDB**), utilizando **FastAPI** e **Beanie** (ODM assíncrono), gerenciado pelo **uv**.

> **Nota Acadêmica:** O arquivo `.env` foi incluído no repositório intencionalmente para facilitar a execução e correção do trabalho, conforme solicitado.

---

## 🚀 Tecnologias Utilizadas

* **Linguagem:** Python 3.12+
* **Framework Web:** FastAPI
* **Banco de Dados:** MongoDB (via Docker)
* **ODM:** Beanie (Motor/Asyncio)
* **Gerenciador:** uv
* **Infraestrutura:** Docker & Docker Compose

---

## 📋 Pré-requisitos

Para rodar este projeto, você precisa apenas de:

1.  **Docker Desktop** (para o banco de dados).
2.  **uv** (para o Python).
    * *Instalação:* `pip install uv`

---

## ⚙️ Como Rodar (Passo a Passo)

### 1. Subir o Banco de Dados
O projeto já conta com um arquivo `docker-compose.yaml` configurado para criar o banco com as credenciais que estão no `.env`.

Abra o terminal na pasta do projeto e execute:

```bash
# Sobe o MongoDB com usuário e senha pré-configurados
docker-compose up -d
```
2. Instalar Dependências

O uv lerá o arquivo pyproject.toml e instalará tudo automaticamente em um ambiente virtual isolado.
Bash
```bash
uv sync
```
3. Iniciar a API

Com o banco rodando e as dependências instaladas, suba o servidor:
```bash
uv run uvicorn app.main:app --reload
```
Acesse a documentação automática para testar: 👉 http://localhost:8000/docs

---

## 🌱 Popular o Banco de Dados

O projeto inclui um script para popular automaticamente o banco com dados realistas usando a biblioteca **Faker**.

### Executando o Script

Com o MongoDB rodando (via Docker), execute:

```bash
uv run python populate_db.py
```

### O que o script faz?

O script `populate_db.py` irá **adicionar novos dados** ao banco (sem apagar os existentes):

- 📋 **12 Proprietários** - com nome, CPF, email e telefone brasileiros
- 🏠 **15 Imóveis** - casas, apartamentos, kitnets, salas comerciais e galpões
- 👥 **15 Inquilinos** - com dados pessoais e renda mensal
- 📝 **12 Contratos** - mistura de contratos ativos e encerrados

### Regras de Negócio Aplicadas

- Imóveis com contratos **ativos** ficam com status `"Alugado"`
- Imóveis sem contrato ativo ficam com status `"Disponivel"`
- Contratos encerrados são gerados com datas no passado
- Valores de aluguel são baseados no tipo de imóvel
