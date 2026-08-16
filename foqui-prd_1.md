# Foqui — Product Requirements Document

**Versão:** 1.0  
**Autora:** Amanda Belo  
**Data:** Abril 2026  
**Status:** Em desenvolvimento

---

## 1. Visão Geral

**Foqui** é uma ferramenta de regulação atencional para profissionais neurodivergentes. Consiste em um pet de desktop discreto e minimalista que serve como âncora visual durante tarefas que exigem atenção sustentada, como reuniões, videoconferências e leitura de documentos longos.

### 1.1 Proposta de Valor

Diferente de desktop pets genéricos focados em entretenimento, o Foqui é posicionado como ferramenta de acessibilidade cognitiva. O pet é o meio, não o fim — ele existe para fornecer estímulo visual sutil que ajuda o cérebro neurodivergente a manter foco sem recorrer a comportamentos visíveis (como fidgeting físico) que podem ser mal interpretados em ambientes profissionais.

### 1.2 Problema

Profissionais com TDAH frequentemente precisam de estímulo secundário para manter atenção em tarefas passivas (ouvir reuniões, assistir apresentações). Soluções físicas como fidget toys ou trabalhos manuais podem ser percebidas como "falta de profissionalismo" por colegas e lideranças. Não existe atualmente uma ferramenta digital projetada especificamente para esse caso de uso.

### 1.3 Solução

Um pet de desktop que:
- Fica sempre visível (always-on-top) mas não intrusivo
- Fornece estímulo visual sutil e contínuo através de animações
- Reage ao contexto de uso do computador
- Pode ser escondido instantaneamente quando necessário
- Tem visual profissional/discreto que não parece "joguinho"

---

## 2. Público-Alvo

### 2.1 Persona Primária

**Profissional neurodivergente (TDAH/TEA) em ambiente corporativo**

- Idade: 25-45 anos
- Trabalha em escritório ou home office
- Participa de reuniões frequentes por videoconferência
- Precisa de estímulo secundário para manter atenção
- Já experimentou fidget toys ou outras estratégias de regulação
- Preocupa-se com percepção profissional

### 2.2 Persona Secundária

**Profissional neurotípico que busca ferramentas de bem-estar digital**

- Interesse em produtividade e foco
- Aprecia gamificação leve
- Busca humanizar o ambiente de trabalho digital

---

## 3. Especificações Técnicas

### 3.1 Plataforma

**MVP:** Windows 10/11  
**Futuro:** macOS, Linux

### 3.2 Stack Tecnológica

| Componente | Tecnologia | Justificativa |
|---|---|---|
| Linguagem | Python 3.11+ | Familiaridade da desenvolvedora, prototipagem rápida |
| Interface | PyQt6 | Suporte nativo a janelas transparentes e frameless |
| Detecção de input | pynput | Monitoramento de teclado/mouse para comportamento reativo |
| Sistema | psutil | Detecção de estado do sistema (idle, janelas abertas) |
| Persistência | JSON local | Configurações e estado do pet |
| Assets | Sprite sheets PNG | Animações frame-by-frame |

### 3.3 Requisitos de Sistema

- Windows 10 versão 1903 ou superior
- 50MB de espaço em disco
- 100MB de RAM
- Não requer conexão com internet

---

## 4. Features por Fase

### 4.1 Core (Semanas 1-2)

Funcionalidades mínimas para o app ser utilizável.

| Feature | Descrição | Prioridade |
|---|---|---|
| Janela transparente | Janela frameless com fundo transparente, always-on-top | P0 |
| Pet arrastável | Arrastar o pet pela tela com mouse | P0 |
| Persistência de posição | Salvar e restaurar posição entre sessões | P0 |
| Animação idle | Respiração e piscada básicas | P0 |
| Atalho esconder/mostrar | Ctrl+Shift+F para toggle de visibilidade | P0 |
| Tray icon | Ícone na bandeja do sistema com menu básico | P0 |

**Critério de sucesso:** Pet visível na tela, arrastável, que sobrevive a reinicializações do app.

### 4.2 MVP (Semanas 3-5)

Funcionalidades que tornam o app útil e agradável.

| Feature | Descrição | Prioridade |
|---|---|---|
| Animações extras | Andando, dormindo, comendo, bocejando | P1 |
| Comportamento reativo | Reações baseadas em contexto do sistema | P1 |
| Sistema de humor | Estados emocionais que influenciam animações | P1 |
| Interação de carinho | Clique no pet dispara animação de carinho | P1 |
| Menu de alimentação | Clique direito para dar comida | P1 |
| Config de tamanho | Slider para ajustar escala do pet (50%-200%) | P1 |
| Config de opacidade | Slider para ajustar transparência (30%-100%) | P1 |
| Janela de configurações | Interface para ajustar preferências | P1 |

**Critério de sucesso:** Usuária consegue usar o app durante uma semana de trabalho real e sente benefício.

### 4.3 v1.1 (Semanas 6-8)

Funcionalidades que enriquecem a experiência.

| Feature | Descrição | Prioridade |
|---|---|---|
| Animações temáticas | Fazendo crochê, ouvindo música, espirrando | P2 |
| Skins adicionais | Ratinho, gato, robô | P2 |
| Timer Pomodoro | Timer sutil no tooltip do pet | P2 |
| Modo apresentação | Detecta compartilhamento de tela e esconde | P2 |
| Estatísticas | Tempo de uso, interações, humor médio | P2 |
| Onboarding | Tutorial de primeiro uso | P2 |

### 4.4 Futuro (Backlog)

| Feature | Descrição |
|---|---|
| Integração com calendário | Ativa automaticamente em reuniões |
| Mais skins | Cachorro, mouse Microsoft, coelho |
| Lojinha de acessórios | Customização visual com itens desbloqueáveis |
| Sync entre dispositivos | Backup na nuvem do estado do pet |
| Versão macOS | Port para sistema Apple |
| Sons opcionais | Efeitos sonoros sutis (desativados por padrão) |

---

## 5. Comportamento do Pet

### 5.1 Sistema de Contexto

O pet monitora o estado do sistema e ajusta seu comportamento de acordo.

| Contexto Detectado | Como Detectar | Comportamento do Pet |
|---|---|---|
| Digitação ativa | pynput keyboard listener | Fica curioso, olha pro lado, orelhas/olhos atentos |
| Mouse ativo | pynput mouse listener | Acompanha levemente com o olhar |
| Idle curto (5-15 min) | Tempo sem input | Boceja, espreguiça |
| Idle longo (15+ min) | Tempo sem input | Deita, fecha olhos, dorme |
| Muitas janelas | psutil window count | Olha pros lados, expressão levemente preocupada |
| Horário noturno (22h-6h) | System time | Sonolento, pisca devagar, prefere ficar deitado |
| Volta de inatividade | Input após idle | Acorda animado, sacode, celebra |
| Após interação | Carinho ou comida | Feliz, pula, coração aparece |

### 5.2 Sistema de Humor

O pet tem estados emocionais que influenciam a frequência e tipo de animações.

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   CONTENTE ←──(carinho/comida)── FELIZ (default)   │
│       │                             │               │
│       │                             │               │
│       ▼                             ▼               │
│   (decay 2h)                   (sem interação 4h)  │
│       │                             │               │
│       ▼                             ▼               │
│    FELIZ ◄────────────────────── NEUTRO            │
│                                     │               │
│                                     ▼               │
│                              (sem interação 8h)    │
│                                     │               │
│                                     ▼               │
│                                 SONOLENTO          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Importante:** O pet NUNCA fica triste, com fome, doente ou em estado que gere culpa. O pior estado é "sonolento", que apenas significa mais animações de descanso. Isso é intencional para não adicionar mais uma fonte de ansiedade para usuárias neurodivergentes.

| Estado | Gatilho | Comportamento |
|---|---|---|
| Feliz | Estado padrão | Animações variadas, ocasionalmente faz atividades (crochê, música) |
| Contente | Após carinho ou comida | Mais ativo, mais animações de celebração, dura ~30min |
| Neutro | Sem interação por 4h+ | Animações mais quietas, mais tempo parado |
| Sonolento | Sem interação por 8h+ ou horário noturno | Prefere ficar deitado, boceja frequentemente, dorme mais |

### 5.3 Animações

**Sprite sheet specifications:**
- Formato: PNG com transparência
- Tamanho base: 64x64 pixels por frame
- Escala: 50% a 200% via config
- FPS: 8 frames por segundo

| Animação | Frames | Loop | Gatilho |
|---|---|---|---|
| idle_breathe | 4 | Sim | Estado padrão |
| idle_blink | 3 | Não | A cada 3-5 segundos |
| idle_look_around | 6 | Não | Aleatório ou muitas janelas |
| walk_right | 8 | Sim | Aleatório (raro) |
| walk_left | 8 | Sim | Aleatório (raro) |
| sleep_enter | 4 | Não | Transição para dormindo |
| sleep_loop | 4 | Sim | Enquanto dormindo |
| sleep_exit | 4 | Não | Acorda |
| yawn | 6 | Não | Idle curto ou sonolento |
| eat | 8 | Não | Após receber comida |
| pet_reaction | 6 | Não | Após carinho |
| happy_jump | 6 | Não | Estado contente |
| curious | 4 | Não | Digitação ativa |
| crochet | 12 | Sim | Aleatório quando feliz (v1.1) |
| listen_music | 8 | Sim | Aleatório quando feliz (v1.1) |
| sneeze | 6 | Não | Aleatório raro (v1.1) |

---

## 6. Interface

### 6.1 Janela Principal (Pet)

- Frameless e transparente
- Always-on-top
- Arrastável por qualquer ponto
- Tamanho: 64-128px (configurável)
- Clique esquerdo: carinho
- Clique direito: menu contextual

### 6.2 Menu Contextual (Clique Direito)

```
┌──────────────────────┐
│ 🍎 Alimentar         │
│ ──────────────────── │
│ ⚙️  Configurações    │
│ 📊 Estatísticas      │
│ ──────────────────── │
│ 👁️  Esconder (Ctrl+Shift+F) │
│ ❌ Sair              │
└──────────────────────┘
```

### 6.3 Janela de Configurações

```
┌─────────────────────────────────────────────────────────┐
│ Configurações do Foqui                              ✕  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ APARÊNCIA                                               │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Tamanho      [────●────────] 100%                   │ │
│ │ Opacidade    [──────────●──] 85%                    │ │
│ │ Pet          [▼ Sapinho    ]                        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ COMPORTAMENTO                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [✓] Reagir à atividade do sistema                   │ │
│ │ [✓] Modo noturno automático                         │ │
│ │ [✓] Iniciar com Windows                             │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ATALHOS                                                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Esconder/Mostrar    [Ctrl+Shift+F]                  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│                                    [ Salvar ] [ Fechar ]│
└─────────────────────────────────────────────────────────┘
```

### 6.4 Tray Icon

- Ícone do pet atual (sapinho, ratinho, etc.)
- Tooltip: "Foqui - [estado atual]"
- Clique esquerdo: mostrar/esconder pet
- Clique direito: mesmo menu contextual

---

## 7. Assets Visuais

### 7.1 Estilo

- **Categoria:** Flat/minimalista
- **Paleta:** 2-3 cores por pet + preto para detalhes
- **Linhas:** Sem outline ou outline muito sutil (1px)
- **Formas:** Arredondadas, amigáveis
- **Referências:** Ícones do Notion, Figma, Linear

### 7.2 Pets Planejados

| Pet | Prioridade | Cores principais | Notas |
|---|---|---|---|
| Sapinho | MVP | Verde menta, bege | Forma simples (blob com olhos), vibe zen |
| Ratinho | v1.1 | Cinza, rosa | Inspirado nas ratinhas da Amanda |
| Gato | v1.1 | Laranja, bege | Clássico, apelo amplo |
| Robô | v1.1 | Azul, prata | Para quem prefere algo não-animal |
| Mouse Microsoft | Futuro | Branco, preto | Easter egg corporativo |

### 7.3 Fonte dos Assets

- Base: Assets adaptados do Figma Community / Flaticon
- Edição: Figma (ajuste de cores, criação de frames de animação)
- Formato final: Sprite sheets PNG 64x64 por frame

---

## 8. Arquitetura Técnica

### 8.1 Estrutura de Diretórios

```
foqui/
├── main.py                 # Entry point
├── requirements.txt        # Dependências
├── config.json            # Configurações do usuário
├── pet_state.json         # Estado persistido do pet
│
├── src/
│   ├── __init__.py
│   ├── app.py             # Classe principal da aplicação
│   ├── pet_window.py      # Janela transparente do pet
│   ├── pet.py             # Lógica do pet (estado, humor, animações)
│   ├── animation.py       # Gerenciador de sprite sheets
│   ├── context_monitor.py # Monitor de atividade do sistema
│   ├── tray.py            # System tray icon
│   ├── settings.py        # Janela de configurações
│   └── hotkeys.py         # Gerenciador de atalhos globais
│
├── assets/
│   ├── pets/
│   │   ├── frog/
│   │   │   ├── idle.png
│   │   │   ├── walk.png
│   │   │   ├── sleep.png
│   │   │   └── ...
│   │   └── rat/
│   │       └── ...
│   ├── icons/
│   │   ├── tray_frog.png
│   │   └── app_icon.ico
│   └── ui/
│       └── ...
│
└── tests/
    └── ...
```

### 8.2 Fluxo Principal

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌─────────┐    ┌──────────────────┐    ┌─────────────────┐ │
│  │  main   │───▶│   App (PyQt6)    │───▶│   Pet Window    │ │
│  └─────────┘    └──────────────────┘    └─────────────────┘ │
│                          │                       │          │
│                          │                       ▼          │
│                          │              ┌─────────────────┐ │
│                          │              │   Pet Logic     │ │
│                          │              │  (state, mood)  │ │
│                          │              └─────────────────┘ │
│                          │                       ▲          │
│                          ▼                       │          │
│                 ┌──────────────────┐            │          │
│                 │ Context Monitor  │────────────┘          │
│                 │  (pynput/psutil) │                       │
│                 └──────────────────┘                       │
│                          │                                  │
│                          ▼                                  │
│                 ┌──────────────────┐                       │
│                 │    Tray Icon     │                       │
│                 └──────────────────┘                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 8.3 Dependências (requirements.txt)

```
PyQt6>=6.5.0
pynput>=1.7.6
psutil>=5.9.0
```

---

## 9. Cronograma

**Duração total estimada:** 6-8 semanas

| Fase | Semanas | Entregas |
|---|---|---|
| Setup & Core | 1-2 | Ambiente, janela transparente, pet arrastável, persistência |
| MVP Features | 3-4 | Animações, comportamento reativo, humor, interações |
| MVP Polish | 5 | Configurações, tray icon, atalhos, testes |
| v1.1 Features | 6-7 | Animações extras, skins adicionais |
| v1.1 Polish | 8 | Pomodoro, modo apresentação, estatísticas |

### 9.1 Milestones

- **M1 (Semana 2):** Pet visível e arrastável na tela
- **M2 (Semana 4):** Pet reativo e com sistema de humor funcionando
- **M3 (Semana 5):** MVP completo, usável para teste pessoal
- **M4 (Semana 8):** v1.1 pronta para lançamento público

---

## 10. Métricas de Sucesso

### 10.1 Pessoais (MVP)

- [ ] Usar o Foqui em todas as reuniões por 2 semanas consecutivas
- [ ] Sentir redução na necessidade de fidgeting físico visível
- [ ] Não receber comentários negativos sobre postura em reuniões

### 10.2 Produto (Lançamento)

- [ ] 100 downloads no primeiro mês
- [ ] 4+ estrelas de avaliação média
- [ ] 3+ feedbacks positivos de usuários neurodivergentes
- [ ] Menção em pelo menos 1 comunidade de TDAH

### 10.3 Portfólio

- [ ] Repositório GitHub com README completo
- [ ] Documentação de arquitetura
- [ ] Case study publicado no LinkedIn
- [ ] Projeto mencionado em pelo menos 2 entrevistas

---

## 11. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Escopo cresce além do planejado | Alta | Alto | PRD definido, features priorizadas, cortar v1.1 se necessário |
| Dificuldade com PyQt6 transparência | Média | Alto | Pesquisar antes, ter fallback para Tkinter |
| Assets demoram mais que esperado | Alta | Médio | Começar com assets simples, iterar visual depois |
| Detecção de contexto imprecisa | Média | Médio | Começar com detecção simples, refinar com uso |
| Pynput conflita com antivírus | Baixa | Alto | Documentar exceções necessárias, testar em Windows Defender |
| Perda de interesse no projeto | Média | Alto | Usar o app diariamente, celebrar milestones |

---

## 12. Referências

### 12.1 Competidores/Inspirações

- **Desktop Pets genéricos:** DPET, Shimeji, WindowPet
- **Apps de foco para TDAH:** Forest, Finch, Habitica
- **Ferramentas de bem-estar:** Pets Therapy (macOS)

### 12.2 Recursos Técnicos

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [pynput Documentation](https://pynput.readthedocs.io/)
- [Transparent Window PyQt6](https://stackoverflow.com/questions/tagged/pyqt6+transparent)

### 12.3 Assets

- [Figma Community - Animal Icons](https://www.figma.com/community)
- [Flaticon - Flat Animal Packs](https://www.flaticon.com/)

---

## Changelog

| Versão | Data | Alterações |
|---|---|---|
| 1.0 | Abril 2026 | Documento inicial |

---

*Documento criado como parte do processo de desenvolvimento do Foqui, ferramenta de acessibilidade cognitiva para profissionais neurodivergentes.*
