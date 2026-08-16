# Foqui

**Ferramenta de regulação atencional para profissionais neurodivergentes.**

Foqui é um pet de desktop discreto que serve como âncora visual durante tarefas que exigem atenção sustentada, como reuniões e videoconferências. Diferente de desktop pets genéricos, o Foqui é posicionado como ferramenta de acessibilidade cognitiva — o pet fornece estímulo visual sutil que ajuda o cérebro neurodivergente a manter foco.

### Features

- **Janela transparente always-on-top** — O pet fica sempre visível, mas não intrusivo
- **Arrastável** — Posicione onde preferir, a posição é salva automaticamente
- **Balões de fala** — Comentários curtos e sarcásticos, nunca cobranças
- **Três modos prontos** — Reunião, Foco e Relax, a um clique ou `Ctrl+Shift+M`
- **Comportamento reativo** — O pet reage ao que você faz no computador
- **Detecta reunião** — Em call ou tela cheia ele vira observador quieto
- **Sistema de humor** — Estados que influenciam animações (sem culpa!)
- **Atalho rápido** — `Ctrl+Shift+F` para esconder/mostrar instantaneamente
- **Visual minimalista** — Design flat e profissional que não parece "joguinho"

## Por que Foqui?

Profissionais com TDAH frequentemente precisam de estímulo secundário para manter atenção em tarefas passivas. Soluções físicas como fidget toys podem ser mal interpretadas em ambientes profissionais. O Foqui resolve isso oferecendo uma ferramenta digital discreta que:

- Fornece estímulo visual contínuo através de animações sutis
- Pode ser escondido instantaneamente quando necessário
- Tem visual profissional que não chama atenção negativa
- Nunca gera culpa (o pet nunca fica triste ou com fome)

## Instalação

### Requisitos

- Windows 10/11
- Python 3.11+

### Setup

```bash
# Clone o repositório
git clone https://github.com/amandabelo/foqui.git
cd foqui

# Crie um ambiente virtual (recomendado)
python -m venv venv
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Execute
python main.py
```

## Uso

### Controles básicos

| Ação | Como fazer |
|------|------------|
| Mover o pet | Arraste com o mouse |
| Fazer carinho | Clique no pet |
| Menu rápido | Clique direito no pet ou no ícone da bandeja |
| Alimentar | Menu rápido → Alimentar |
| Ver status | Menu rápido → Status (vira um balão, não uma janela) |
| Esconder/Mostrar | `Ctrl+Shift+F` ou clique no ícone da bandeja |
| Trocar de modo | `Ctrl+Shift+M` ou menu rápido |
| Configurações | `Ctrl+Shift+O` ou menu rápido |
| Sair | Menu rápido → Sair |

### Modos

Três presets resolvem quase tudo sem passar pelas configurações. Mexer em
qualquer detalhe manualmente muda o modo para "Personalizado", sem perguntar nada.

| Modo | Como o pet fica |
|------|-----------------|
| 🎧 **Reunião** | Discreto, parado, fala raramente |
| 🎯 **Foco** | Quase invisível, movimento mínimo, sem balões |
| 🌿 **Relax** | Presente, animado e tagarela |

### Comportamentos do pet

| Contexto | Comportamento |
|----------|---------------|
| Você digitando muito | Fica curioso, olha pro lado, comenta de vez em quando |
| Call ou app em tela cheia | Vira observador: só respira e olha, sem andar |
| Mouse parado 5+ min | Boceja, espreguiça |
| Mouse parado 15+ min | Deita e dorme |
| Horário noturno (22h-6h) | Fica sonolento |
| Volta de inatividade | Acorda e comenta que você voltou |
| Mouse parado em cima dele | Reage ao ser encarado |

Ele pisca sozinho a cada 5–8 segundos — animação contínua o suficiente para
ancorar o olhar, discreta o suficiente para não cansar.

### Balões de fala

Frases curtas, sarcásticas e sem cobrança, disparadas por interação (carinho,
comida), por contexto (reunião, noite, volta de inatividade) ou de tempos em
tempos. Dá para escolher entre balão de **fala** e de **pensamento**, ajustar a
frequência (`Nunca` / `Raramente` / `Às vezes` / `Bastante`) ou desligar de vez.

O texto vive em [`src/dialogue.py`](src/dialogue.py) — adicione as suas frases lá.

### Sistema de humor

Os estados descrevem disposição, nunca carência:

- **Consciente** (default) — Animações variadas
- **Relaxado** — Após carinho ou comida, mais ativo
- **Curioso** — Sem interação por um tempo, mais quieto
- **Sonolento** — Sem interação por muito tempo, prefere descansar

O pet **nunca** fica triste, com fome ou doente. O pior que acontece é ele dormir mais. 💚

### Acessibilidade

- Todos os controles principais têm atalho de teclado
- Menu com itens grandes, um ícone por linha, rótulos curtos
- Sliders de tamanho e opacidade com pré-visualização ao vivo
- Intensidade de movimento ajustável (sutil / moderado / animado)
- Som mudo por padrão
- Onboarding de quatro telas, uma frase cada, com opção de pular

## Arquitetura

```
foqui/
├── main.py                 # Entry point
├── requirements.txt        # Dependências
├── config.json            # Configurações do usuário
├── pet_state.json         # Estado persistido do pet
├── src/
│   ├── app.py             # Orquestra todos os componentes
│   ├── pet_window.py      # Janela transparente do pet
│   ├── pet.py             # Lógica do pet (estado, humor)
│   ├── animation.py       # Gerenciador de sprites
│   ├── speech_bubble.py   # Balão de fala/pensamento
│   ├── dialogue.py        # Banco de frases
│   ├── presets.py         # Modos, presença e intensidade
│   ├── context_monitor.py # Monitor de atividade e reunião
│   ├── onboarding.py      # Primeira execução
│   ├── sound.py           # Sons opcionais (mudo por padrão)
│   ├── tray.py            # Bandeja e menu rápido
│   ├── settings.py        # Janela de configurações
│   └── hotkeys.py         # Atalhos globais
├── assets/                # Sprites, ícones e sons (ver assets/README.md)
└── tests/
```

### Testes

```bash
python -m unittest discover -s tests
```

O smoke test sobe o app inteiro em modo offscreen — não precisa de tela.

## Tech Stack

- **Python 3.11+**
- **PyQt6** — Interface e janela transparente
- **pynput** — Monitoramento de input
- **psutil** — Info do sistema

## Roadmap

- [x] MVP funcional
- [x] Balões de fala, modos prontos e onboarding
- [x] Trocar de skin sem reiniciar
- [ ] Sprites de verdade (hoje cada tipo é um placeholder desenhado em código, com cor e acessório próprios)
- [x] Animações temáticas (crochê, música, café, maçã, chocolate)
- [ ] Timer Pomodoro
- [ ] Modo apresentação

## Autora

**Amanda Belo** — Desenvolvido como ferramenta pessoal de acessibilidade e projeto de portfólio.
