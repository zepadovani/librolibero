# Plano de Desenvolvimento: Librolibero GUI (Multi-OS)

Este documento estabelece as fases e etapas para o desenvolvimento de uma Interface Gráfica de Usuário (GUI) multiplataforma para o `librolibero`. O plano foi estruturado para **otimizar ao máximo o uso de tokens e a janela de contexto** durante a programação com agentes de IA, priorizando a modularidade, separação de responsabilidades (MVC/MVVM) e implementação iterativa.

## Diretrizes de Otimização para Agentes de IA
Para garantir que o agente não se perca no contexto e consuma menos tokens:
1. **Separação Estrita (Core vs. GUI):** A lógica de negócio (`scanner`, `zotero_client`, `metadata`) nunca deve saber da existência da GUI. Elas se comunicam via callbacks ou eventos.
2. **Arquivos Pequenos e Modulares:** Cada tela (Configuração, Execução, Logs) deve ter seu próprio arquivo (ex: `gui_config.py`, `gui_main.py`). Limite arquivos a ~200-300 linhas.
3. **Desenvolvimento Iterativo:** Peça ao agente para implementar uma fase ou etapa de cada vez. Não peça a GUI inteira de uma vez.
4. **Mocking Inicial:** Teste a GUI com dados falsos (mocks) antes de conectá-la ao core pesado.

---

## Fase 1: Escolha Tecnológica e Arquitetura Base
**Objetivo:** Definir o framework e a estrutura de pastas sem alterar o código existente.

* [ ] **Etapa 1.1:** Vamos implementar PySide6 (Qt para Python) 
* [ ] **Etapa 1.2:** Criar estrutura de diretórios.
  * Criar pasta `librolibero/gui/` com `__init__.py`.
  * Atualizar `pyproject.toml` ou `requirements.txt` com a dependência escolhida.
* [ ] **Etapa 1.3:** Criar o módulo principal da janela (`librolibero/gui/app.py`) apenas com o esqueleto (janela vazia).

## Fase 2: Tela de Configuração e Credenciais
**Objetivo:** Coletar Zotero ID e API Key do usuário de forma amigável.

* [ ] **Etapa 2.1:** Criar o componente `ConfigFrame` (`librolibero/gui/config_view.py`).
* [ ] **Etapa 2.2:** Adicionar campos de input para `Zotero User ID` e `Zotero API Key`.
* [ ] **Etapa 2.3:** Adicionar textos de ajuda e links explicativos na interface:
  * *Onde achar o User ID:* Explicar que está na página [Settings > Feeds/API](https://www.zotero.org/settings/keys).
  * *Como criar a API Key:* Explicar que deve ser gerada na mesma página com permissões de escrita ("Write").
* [ ] **Etapa 2.4:** Criar botão "Salvar" que utiliza o módulo `config.py` existente para gravar no disco.

## Fase 3: Seleção de Diretórios e Opções de Scanner
**Objetivo:** Permitir que o usuário escolha onde estão os PDFs/eBooks.

* [ ] **Etapa 3.1:** Criar o componente `ScannerFrame` (`librolibero/gui/scanner_view.py`).
* [ ] **Etapa 3.2:** Adicionar um botão "Escolher Pasta..." que abre um diálogo nativo do SO (`filedialog`).
* [ ] **Etapa 3.3:** Mostrar o caminho da pasta escolhida em um campo de texto (somente leitura).
* [ ] **Etapa 3.4:** Adicionar Checkbox "Vasculhar subpastas" (Recursivo), ativado por padrão.

## Fase 4: Integração Multithreading e Tela de Execução
**Objetivo:** Executar o scanner sem travar a interface gráfica (congelamento de UI).

* [ ] **Etapa 4.1:** Criar um gerenciador de Threads (`librolibero/gui/worker.py`) para encapsular chamadas de `scanner.py` e `zotero_client.py`.
* [ ] **Etapa 4.2:** Criar o componente `ProgressFrame` (`librolibero/gui/progress_view.py`).
* [ ] **Etapa 4.3:** Adicionar uma barra de progresso e uma caixa de texto de log (LogBox) para mostrar:
  * "Buscando arquivos..."
  * "Extraindo metadados de X.pdf..."
  * "Enviando para o Zotero..."
* [ ] **Etapa 4.4:** Conectar eventos do `Worker` aos componentes visuais (atualizar barra e log).

## Fase 5: Ajustes Finais e Refinamento
**Objetivo:** Polimento da aplicação.

* [ ] **Etapa 5.1:** Lógica de Navegação: O app deve verificar se as credenciais já existem. Se não, mostrar a Tela de Configuração. Se sim, ir direto para a Tela de Scanner.
* [ ] **Etapa 5.2:** Tratamento de erros visuais (Mostrar pop-ups de erro se a API Key for inválida ou se não houver internet).

## Fase 6: Empacotamento para Distribuição (Multi-OS)
**Objetivo:** Gerar executáveis para Windows, macOS e Linux.

* [ ] **Etapa 6.1:** Configurar script do **PyInstaller** (`build_gui.py` ou comando no `pyproject.toml`).
* [ ] **Etapa 6.2:** Adicionar ícones da aplicação (arquivos `.ico` e `.icns`).
* [ ] **Etapa 6.3:** Testar a compilação garantindo que as dependências do core (como bibliotecas de manipulação de PDF) estão sendo incluídas corretamente no executável.
