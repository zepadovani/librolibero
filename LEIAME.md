# librolibero

Um importador de linha de comando que rastreia uma pasta de PDFs e EPUBs, extrai ISBNs, busca metadados bibliográficos em serviços online e cria itens do tipo *book* no Zotero com arquivo vinculado (*linked file*), compatível com o plugin ZotMoov.

## Descrição

`librolibero` automatiza o processo de importação de uma coleção de livros para o Zotero. Ele:

1. **Escaneia** uma pasta em busca de PDFs e EPUBs
2. **Extrai ISBNs** dos nomes de arquivo ou do conteúdo dos documentos
3. **Resolve metadados** bibliográficos via APIs em cascata (isbnlib, Open Library, Google Books)
4. **Detecta duplicatas** no Zotero e oferece opções interativas de tratamento
5. **Cria itens** no Zotero com arquivo vinculado
6. **Opcionalmente move** arquivos para a lixeira após importação bem-sucedida

### Caso de uso

Importar coleções de livros cujos nomes de arquivo seguem um padrão estruturado:
```
Título -- Autor -- Ano -- Editora -- isbn13 XXXXXXXXXXXXX -- hash -- sufixo.pdf
```

## Requisitos

- Python 3.8+
- Credenciais da API do Zotero (ID e chave de acesso)

## Instalação

### Via pip

```bash
pip install -e .
```

Ou instalar as dependências diretamente:

```bash
pip install -r requirements.txt
```

### Dependências

- **pyzotero** — acesso à API do Zotero
- **isbnlib** — resolução de metadados via ISBN
- **pymupdf** (fitz) — extração de ISBN de PDFs
- **ebooklib** — extração de metadados de EPUBs
- **requests** — requisições HTTP
- **tomli** — leitura de arquivos TOML
- **python-dotenv** — carregamento de variáveis de ambiente
- **send2trash** — move arquivos para lixeira com segurança

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.nosync/.env` na raiz do projeto com suas credenciais do Zotero:

```env
ZOTERO_ID=seu_user_id_aqui
zoteroKEY=sua_api_key_aqui
```

**Obtenção das credenciais:**
1. Acesse [zotero.org/settings/keys](https://www.zotero.org/settings/keys)
2. Crie uma nova chave de acesso com permissão de escrita
3. Seu User ID está disponível em [zotero.org/settings/profile](https://www.zotero.org/settings/profile)

### Arquivo de Configuração

Opcionalmente, crie um arquivo `config.toml` na raiz do projeto para personalizar o comportamento:

```toml
[config]
directory = "books/"
extensions = [".pdf", ".epub"]
zotmoov_mode = false
```

**Parâmetros:**

- **directory** — caminho da pasta contendo os livros (padrão: `books/`)
- **extensions** — extensões de arquivo a processar (padrão: `[".pdf", ".epub"]`)
- **zotmoov_mode** — quando `true`, suprime o comportamento de lixeira do `--trash-after-import` pois o plugin ZotMoov move os arquivos automaticamente (padrão: `false`)

## Uso

### Comando Básico

```bash
python -m librolibero
```

Processa todos os arquivos na pasta padrão (`books/`) e os importa para o Zotero.

### Opções de Linha de Comando

```bash
python -m librolibero --help
```

**Opções disponíveis:**

- `--dir DIR` — pasta fonte contendo os livros (sobrescreve `config.toml`)
- `--dry-run` — executa sem enviar requisições POST ao Zotero; apenas mostra o que seria feito
- `--trash-after-import` — move arquivos para a lixeira após importação bem-sucedida (ignorado se `zotmoov_mode=true`)

### Exemplos

**Teste sem alterar nada:**
```bash
python -m librolibero --dry-run
```

**Importar de uma pasta específica:**
```bash
python -m librolibero --dir /caminho/para/meus_livros
```

**Importar e mover arquivos para lixeira:**
```bash
python -m librolibero --trash-after-import
```

## Pipeline de Execução

O fluxo de processamento segue este diagrama:

```
scan_and_extract()
    ↓
    extract_isbn_from_filename()
         └→ extract_isbn_from_content() [fallback]
    ↓
resolve_metadata(isbn)
    ├→ isbnlib merge
    ├→ isbnlib openl [fallback]
    ├→ Open Library REST [fallback]
    ├→ Google Books REST [fallback]
    └→ resolve_metadata_from_filename() [fallback final]
    ↓
import_file()
    ├→ find_existing_by_isbn() [detecta duplicatas]
    ├→ create_item() [cria novo item no Zotero]
    └→ attach_linked_file() [anexa arquivo vinculado]
    ↓
send2trash() [opcional, se --trash-after-import]
```

### Etapas Detalhadas

#### 1. Escanear Arquivos
Rastreia a pasta e lista todos os arquivos com extensões configuradas (`.pdf`, `.epub`).

#### 2. Extrair ISBN
Tenta extrair ISBN em ordem de prioridade:
1. Padrão explícito `isbn13 XXXXXXXXXXXXX` (nomes estruturados com ISBN destacado)
2. ISBN-13 genérico (13 dígitos consecutivos)
3. ISBN-10 genérico (9 dígitos + dígito de controle)
4. **Fallback:** lê o conteúdo do arquivo (primeiras 5 páginas de PDF ou metadados de EPUB)

#### 3. Resolver Metadados
Busca informações bibliográficas via APIs em cascata:
- isbnlib (merge)
- isbnlib (openl)
- Open Library REST
- Google Books REST
- Fallback: extrai título e ano do nome do arquivo

#### 4. Importar para Zotero
Antes de criar, verifica se já existe um item com o mesmo ISBN:
- **Duplicata encontrada:**
  - Pergunta ao usuário (ou usa estratégia global)
  - Opções: ignorar, criar novo item, ou anexar ao existente
- **Sem duplicata:**
  - Cria novo item no Zotero
  - Anexa arquivo como linked file

#### 5. Limpeza Opcional
Se `--trash-after-import` for usado (e não estiver em `zotmoov_mode`), move o arquivo para a lixeira.

## Estrutura do Projeto

```
librolibero/
├── __init__.py           # Versão do pacote
├── __main__.py           # Ponto de entrada (python -m librolibero)
├── cli.py                # Interface de linha de comando (argparse)
├── config.py             # Carregamento de .env e config.toml
├── scanner.py            # Rastreamento de arquivos e extração de ISBN
├── metadata.py           # Busca de metadados via APIs
├── zotero_client.py      # Integração com a API do Zotero
└── report.py             # Logging e resumo final
```

## Logs

Os logs de importação são salvos em `logs/import_YYYY-MM-DD.log` com informações detalhadas sobre cada arquivo processado, sucessos, falhas e avisos.

## Tratamento de Duplicatas

Quando o mesmo ISBN já existe no Zotero, o programa oferece opções interativas:

```
1) Ignorar este arquivo
2) Criar novo item mesmo assim
3) Anexar ao item existente (mais recente)
4) Ignorar TODOS os próximos duplicados
5) Criar novos itens para TODOS os próximos duplicados
6) Anexar TODOS os próximos duplicados ao item existente
```

Escolher opção 4, 5 ou 6 aplica a estratégia a todos os próximos arquivos, evitando perguntas repetidas.

## Troubleshooting

### "ZOTERO_ID ou zoteroKEY não encontrado"
Certifique-se de que o arquivo `.nosync/.env` existe e contém as credenciais corretas.

### "Metadados não encontrados"
Se o ISBN não for extraído corretamente, o programa tenta extrair metadados do nome do arquivo. Verifique se o formato do nome está próximo ao esperado (título, autor, ano).

### ZotMoov Mode
Se usar o plugin ZotMoov, configure `zotmoov_mode = true` no `config.toml` para evitar conflitos com o gerenciamento automático de arquivos.

## Licença

Este programa é um software livre: você pode redistribuí-lo e/ou modificá-lo sob os termos da Licença Pública Geral GNU (GNU General Public License) conforme publicada pela Free Software Foundation, seja a versão 3 da Licença ou (a seu critério) qualquer versão posterior.

Consulte o arquivo [LICENSE](LICENSE) para obter mais detalhes.