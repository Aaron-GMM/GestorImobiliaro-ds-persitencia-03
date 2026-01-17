# Diagrama de Classes do Sistema (NoSQL / MongoDB)

Este diagrama representa a estrutura das coleções (Collections) no MongoDB e como os documentos se relacionam utilizando o ODM **Beanie**.

Diferente do modelo relacional anterior, as relações aqui são feitas através de referências (`Links`) armazenadas nos documentos filhos.

```mermaid
classDiagram
    direction RL

    %% Coleção de Proprietários
    class Proprietario {
        +ObjectId id
        +String nome
        +String cpf
        +String email
        +String telefone
        +String endereco
    }

    %% Coleção de Imóveis
    class Imovel {
        +ObjectId id
        +String apelido_imovel
        +String descricao
        +String endereco
        +Float valor_aluguel_base
        +String tipo_imovel
        +String status
        +Link~Proprietario~ proprietario
    }

    %% Coleção de Inquilinos
    class Inquilino {
        +ObjectId id
        +String nome
        +String cpf
        +String email
        +String telefone
        +Float renda_mensal
    }

    %% Coleção de Contratos
    class Contrato {
        +ObjectId id
        +Link~Inquilino~ inquilino
        +Link~Imovel~ imovel
        +Date data_inicio
        +Date data_fim
        +Float valor_aluguel
        +String status
    }

    %% Relacionamentos (Referências)
    %% O Imóvel guarda uma referência ao Proprietário
    Imovel "0..*" --> "1" Proprietario : Referencia (Link)

    %% O Contrato guarda referências ao Imóvel e ao Inquilino
    Contrato "0..*" --> "1" Imovel : Referencia (Link)
    Contrato "0..*" --> "1" Inquilino : Referencia (Link)