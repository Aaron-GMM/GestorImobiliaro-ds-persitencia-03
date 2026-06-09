"""
Script para popular o banco de dados MongoDB com dados realistas.
Utiliza a biblioteca Faker para gerar dados brasileiros.
"""
import asyncio
import random
from datetime import date, timedelta, datetime
from faker import Faker
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.proprietario import Proprietario
from app.models.imovel import Imovel
from app.models.inquilino import Inquilino
from app.models.contrato import Contrato
from app.models.pagamento import Pagamento, Encargo

# Configurar Faker para dados em português brasileiro
fake = Faker('pt_BR')

# Tipos de imóveis disponíveis
TIPOS_IMOVEL = ["Casa", "Apartamento", "Kitnet", "Sala Comercial", "Galpão"]

# Apelidos para imóveis (combinações realistas)
APELIDOS_IMOVEL = [
    "Casa da Praia", "Apartamento Centro", "Kitnet Universitária",
    "Casa Verde", "Apto Jardim", "Cobertura Duplex", "Flat Executivo",
    "Studio Moderno", "Casa Colonial", "Sobrado Familiar", "Loft Industrial",
    "Apartamento Vista Mar", "Casa de Campo", "Sala Comercial Centro",
    "Galpão Industrial"
]


async def init_database():
    """Inicializa a conexão com o banco de dados."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[Proprietario, Imovel, Inquilino, Contrato, Pagamento, Encargo],
    )
    print("Conexão com MongoDB estabelecida!")


async def limpar_banco():
    """Remove todos os documentos das coleções."""
    await Pagamento.delete_all()
    await Encargo.delete_all()
    await Contrato.delete_all()
    await Imovel.delete_all()
    await Inquilino.delete_all()
    await Proprietario.delete_all()
    print("Banco de dados limpo!")


async def criar_proprietarios(quantidade: int = 12) -> list[Proprietario]:
    """
    Cria proprietários com dados realistas brasileiros.

    Args:
        quantidade: Número de proprietários a criar.

    Returns:
        Lista de proprietários criados.
    """
    proprietarios = []

    for _ in range(quantidade):
        prop = Proprietario(
            nome=fake.name(),
            email=fake.email(),
            senha=fake.password(length=12, special_chars=True, digits=True, upper_case=True),
            endereco=fake.address()
        )
        await prop.insert()
        proprietarios.append(prop)

    print(f"👤 {quantidade} proprietários criados!")
    return proprietarios


async def criar_imoveis(proprietarios: list[Proprietario], quantidade: int = 15) -> list[Imovel]:
    """
    Cria imóveis associados a proprietários existentes.

    Args:
        proprietarios: Lista de proprietários disponíveis.
        quantidade: Número de imóveis a criar.

    Returns:
        Lista de imóveis criados.
    """
    imoveis = []
    apelidos_usados = set()

    for i in range(quantidade):
        # Gerar apelido único
        apelido_base = random.choice(APELIDOS_IMOVEL)
        apelido = f"{apelido_base} {i+1}" if apelido_base in apelidos_usados else apelido_base
        apelidos_usados.add(apelido)

        tipo = random.choice(TIPOS_IMOVEL)

        # Valor baseado no tipo de imóvel
        valores_base = {
            "Casa": (1500, 5000),
            "Apartamento": (1200, 4000),
            "Kitnet": (600, 1200),
            "Sala Comercial": (800, 3000),
            "Galpão": (2000, 8000)
        }
        valor_min, valor_max = valores_base.get(tipo, (1000, 3000))

        imovel = Imovel(
            apelido_imovel=apelido,
            descricao=f"{tipo} com {random.randint(1, 4)} quartos, {random.randint(1, 3)} banheiros. {fake.sentence()}",
            endereco=fake.address(),
            valor_aluguel_base=round(random.uniform(valor_min, valor_max), 2),
            tipo_imovel=tipo,
            status="Disponivel",
            proprietario=random.choice(proprietarios)
        )
        await imovel.insert()
        imoveis.append(imovel)

    print(f"🏠 {quantidade} imóveis criados!")
    return imoveis


async def criar_inquilinos(proprietarios: list[Proprietario], quantidade: int = 15) -> list[Inquilino]:
    """
    Cria inquilinos com dados realistas brasileiros.

    Args:
        quantidade: Número de inquilinos a criar.

    Returns:
        Lista de inquilinos criados.
    """
    inquilinos = []

    for _ in range(quantidade):
        inquilino = Inquilino(
            nome=fake.name(),
            cpf=fake.cpf(),
            email=fake.email(),
            telefone=fake.cellphone_number(),
            renda_mensal=round(random.uniform(2000, 15000), 2),
            proprietario=random.choice(proprietarios)
        )
        await inquilino.insert()
        inquilinos.append(inquilino)

    print(f"👥 {quantidade} inquilinos criados!")
    return inquilinos


async def criar_contratos(
    inquilinos: list[Inquilino],
    imoveis: list[Imovel],
    proprietarios: list[Proprietario],
    quantidade: int = 12
) -> list[Contrato]:
    """
    Cria contratos de aluguel entre inquilinos e imóveis.

    Regras:
    - Um imóvel só pode ter um contrato ativo por vez
    - Contratos ativos atualizam o status do imóvel para "Alugado"

    Args:
        inquilinos: Lista de inquilinos disponíveis.
        imoveis: Lista de imóveis disponíveis.
        proprietarios: Lista de proprietários disponíveis.
        quantidade: Número de contratos a criar.

    Returns:
        Lista de contratos criados.
    """
    contratos = []
    imoveis_disponiveis = [i for i in imoveis if i.status == "Disponivel"]

    # Criar alguns contratos ativos
    contratos_ativos = min(quantidade // 2, len(imoveis_disponiveis))

    for i in range(contratos_ativos):
        imovel = imoveis_disponiveis[i]
        inquilino = random.choice(inquilinos)
        proprietario = imovel.proprietario

        # Contrato ativo - começou há alguns meses, termina no futuro
        data_inicio = date.today() - timedelta(days=random.randint(30, 180))
        data_fim = data_inicio + timedelta(days=random.randint(365, 730))
        dia_vencimento = random.randint(1, 10)  # Vencimento entre dia 1 e 10

        contrato = Contrato(
            inquilino=inquilino,
            imovel=imovel,
            data_inicio=data_inicio,
            data_fim=data_fim,
            valor_aluguel=round(imovel.valor_aluguel_base * random.uniform(0.95, 1.1), 2),
            dia_vencimento=dia_vencimento,
            status="Ativo",
            proprietario=proprietario
        )
        await contrato.insert()
        contratos.append(contrato)

        # Atualizar status do imóvel
        await imovel.set({"status": "Alugado"})

    # Criar alguns contratos encerrados (histórico)
    contratos_encerrados = quantidade - contratos_ativos

    for _ in range(contratos_encerrados):
        imovel = random.choice(imoveis)
        inquilino = random.choice(inquilinos)
        proprietario = imovel.proprietario

        # Contrato encerrado - no passado
        data_fim = date.today() - timedelta(days=random.randint(30, 365))
        data_inicio = data_fim - timedelta(days=random.randint(180, 730))
        dia_vencimento = random.randint(1, 10)

        status = random.choice(["Encerrado", "Cancelado"])

        contrato = Contrato(
            inquilino=inquilino,
            imovel=imovel,
            data_inicio=data_inicio,
            data_fim=data_fim,
            valor_aluguel=round(imovel.valor_aluguel_base * random.uniform(0.9, 1.05), 2),
            dia_vencimento=dia_vencimento,
            status=status,
            proprietario=proprietario
        )
        await contrato.insert()
        contratos.append(contrato)

    print(f"📄 {quantidade} contratos criados ({contratos_ativos} ativos, {contratos_encerrados} encerrados)!")
    return contratos


async def criar_pagamentos(contratos: list[Contrato]) -> list[Pagamento]:
    """
    Cria pagamentos para contratos ativos.

    Args:
        contratos: Lista de contratos disponíveis.

    Returns:
        Lista de pagamentos criados.
    """
    pagamentos = []
    contratos_ativos = [c for c in contratos if c.status == "Ativo"]

    for contrato in contratos_ativos:
        # Calcular número de meses desde o início do contrato
        meses_contrato = ((contrato.data_fim.year - contrato.data_inicio.year) * 12 +
                         (contrato.data_fim.month - contrato.data_inicio.month))

        # Criar pagamentos para alguns meses (não todos)
        num_pagamentos = min(random.randint(3, 6), meses_contrato)

        for i in range(num_pagamentos):
            # Calcular data de vencimento baseada no dia_vencimento do contrato
            ano = contrato.data_inicio.year + (contrato.data_inicio.month + i - 1) // 12
            mes = (contrato.data_inicio.month + i - 1) % 12 + 1
            data_vencimento = date(ano, mes, contrato.dia_vencimento)

            # Determinar status do pagamento
            dias_atraso = (date.today() - data_vencimento).days
            if dias_atraso > 5:
                status = random.choice(["Atrasado", "Pago"])
            elif dias_atraso < 0:
                status = "Pendente"
            else:
                status = random.choice(["Pendente", "Pago"])

            # Calcular multa e juros se estiver atrasado
            multa = 0.0
            juros = 0.0
            if status == "Atrasado":
                multa = contrato.valor_aluguel * 0.02  # 2% de multa
                juros = contrato.valor_aluguel * 0.0033 * max(0, dias_atraso)  # 0.33% ao dia

            valor_total = contrato.valor_aluguel + multa + juros

            # Data de pagamento se estiver pago
            data_pagamento = None
            if status == "Pago":
                data_pagamento = data_vencimento + timedelta(days=random.randint(0, 5))

            numero_parcela = f"{i+1:02d}/{meses_contrato:02d}"

            pagamento = Pagamento(
                contrato=contrato,
                numero_parcela=numero_parcela,
                data_vencimento=data_vencimento,
                valor_original=round(contrato.valor_aluguel, 2),
                multa=round(multa, 2),
                juros=round(juros, 2),
                valor_total=round(valor_total, 2),
                status=status,
                data_pagamento=data_pagamento,
                proprietario=contrato.proprietario
            )
            await pagamento.insert()
            pagamentos.append(pagamento)

    print(f"💰 {len(pagamentos)} pagamentos criados!")
    return pagamentos


async def criar_encargos(proprietarios: list[Proprietario]) -> list[Encargo]:
    """
    Cria configurações de encargos para proprietários.

    Args:
        proprietarios: Lista de proprietários disponíveis.

    Returns:
        Lista de encargos criados.
    """
    encargos = []

    for proprietario in proprietarios:
        # Criar encargo com valores padrão ou aleatórios
        encargo = Encargo(
            multa_percentual=round(random.uniform(1.0, 5.0), 2),
            juros_mora=round(random.uniform(0.1, 1.0), 2),
            tolerancia_dias=random.randint(0, 5),
            valor_minimo_multa=round(random.uniform(0.0, 50.0), 2),
            proprietario=proprietario
        )
        await encargo.insert()
        encargos.append(encargo)

    print(f"⚙️ {len(encargos) } encargos criados!")
    return encargos


async def main():
    """Função principal para popular o banco de dados."""
    print("=" * 50)
    print(" Iniciando população do banco de dados...")
    print("=" * 50)

    await init_database()

    # Limpar banco de dados antes de criar novos dados
    await limpar_banco()

    # Criar dados
    proprietarios = await criar_proprietarios(12)
    imoveis = await criar_imoveis(proprietarios, 15)
    inquilinos = await criar_inquilinos(proprietarios, 15)
    contratos = await criar_contratos(inquilinos, imoveis, proprietarios, 12)
    pagamentos = await criar_pagamentos(contratos)
    encargos = await criar_encargos(proprietarios)

    print("=" * 50)
    print("Banco de dados populado com sucesso!")
    print(f"   - {len(proprietarios)} proprietários")
    print(f"   - {len(imoveis)} imóveis")
    print(f"   - {len(inquilinos)} inquilinos")
    print(f"   - {len(contratos)} contratos")
    print(f"   - {len(pagamentos)} pagamentos")
    print(f"   - {len(encargos)} encargos")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
