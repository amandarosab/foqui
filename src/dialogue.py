"""
DialogueBank - Banco de falas do Foqui

Regras de tom (do PRD):
- humor sarcástico e leve, nunca punitivo
- sem cobrança, sem culpa, sem "estou com fome / estou triste"
- frases curtas: cabem em um balão sem virar parágrafo
"""

from collections import deque
from typing import Optional
import random


# Cada categoria é um gatilho de contexto. Frases curtas, no máximo ~90 caracteres.////
PHRASES = {
    # Primeira vez que aparece na sessão
    "hello": [
        "Oii. Eu sou o Foqui! Não sei se você gosta de pets, mas eu gosto de você",
        "Oii. Eu sou o Foqui! Tô aqui só pra lembrar que você existe",
        "Cheguei. Não precisa fazer nada com essa informação",
        "Presente! Digo eu, não você...",
    ],

    # Clique esquerdo = carinho
    "pet": [
        "Ah, carinho. Meu formato favorito de interrupção!",
        "Isso. Continua... Eu aceito elogios também",
        "Obrigado. Eu não sei se mereço, mas aceito rs",
        "Você tem bom gosto para pets flutuantes",
        "Registrado no meu banco de dados emocional",
    ],

    # Alimentar
    "feed": [
        "Hmm. Muito bom",
        "Obrigado. Não precisava, mas aceito",
        "Que delícia! Eu não como, mas imagino que seja bom",
        ],

    # Voltou depois de um tempo longe
    "welcome_back": [
        "Que bom que você voltou, pensei que tinha sumido!.",
        "Olha só quem decidiu reaparecer na própria tela",
        "Uhuu, olha quem tá de volta!",
        "Oi, você voltou! Eu tava com saudade",
    ],

    # Conversa ambiente (ociosa), sem gatilho específico
    "idle": [
        "Você pode se sentir confortável comigo",
        "Se serve de consolo, eu também não sei que horas são",
        "Respira, respira. Eu já respirei três vezes só nesse balão",
    ],

    # Digitando muito
    "typing": [
        "Uau, você tá produzindo horrores hein...",
        "Esse teclado tá levando uma baita surra. Tá tudo bem aí?",
        "Curioso pra saber o que você tá escrevendo. Mas não vou ler, prometo (é contra minha política de privacidade!)",
    ],

    # Reunião / call detectada
    "meeting": [
        "Modo observador ativado. Vou ficar de canto julgando em silêncio.",
        "Reunião? Beleza, eu fico quietinho aqui na frente",
        "Você não tá sozinho nessa call. Tecnicamente",
    ],
    "meeting_end": [
        "Ufaa, acabou a reunião!",
        "Você sobreviveu!",
        "Reunião encerrada, pode desfazer a cara de reunião",
    ],

    # Noite
    "night": [
        "Já tá tarde, né? Que tal fazer uma pausa?",
        "Eu já tô meio sonolento. Você também?",
        "Hora de desligar. Eu também vou dormir, prometo",
    ],

    # Vai esconder (Ctrl+Shift+F)
    "hide": [
        "Sumindo. Volto quando você chamar",
        "Até mais. Vou me esconder na sua tela",
        "Tá bom, eu entendo. Modo invisível",
        "Tchauzinho. Vou me esconder, mas não se esquece de mim",
    ],
    "show": [
        "Voltei!",
        "Opa, você me chamou?"
        "Oii, voltei! Sentiu a minha falta?",
        "Oii, tô de volta! Não gosto de ficar sozinho por muito tempo",
    ],

    # Troca de modo
    "mode_meeting": [
        "Modo reunião. Vou ser discreto, presente e levemente elegante",
    ],
    "mode_focus": [
        "Modo foco. Vou ficar quase invisível. Eu disse quase...",
        "Modo foco. Vou ficar quietinho, mas não sumo totalmente",
    ],
    "mode_relax": [
        "Modo relax. Agora eu falo demais, depois não reclama hein!",
        "Modo relax. Vou ficar mais falante, mas não se preocupe, é só um balão",
        "Modo relax. Vou ficar mais solto, mas não se preocupe, é só um balão",
    ],

    # Hover longo
    "hover": [
        "Você tá me encarando?",
        "Tá me encarando. Eu sei. Não precisa se explicar",
        "Sim, eu pisco. Obrigado por notar",
        "To sentindo uma coceirinha no nariz, pode coçar pra mim?",
    ],

    # Acordou
    "wake": [
        "Ops, eu cochilei",
        "Acordei. Cadê o café? Ah, é, eu não bebo",
        "Acordei. Tô pronto pra mais um dia de tela",
        "Bom dia! Eu não durmo, mas gosto de acordar com você",
    ],

    # Configurações salvas
    "settings_saved": [
        "Anotado. Prometo tentar obedecer",
        "Ajustado. Ficou melhor assim, admito!",
    ],

    # Hobbies que o pet puxa sozinho enquanto ocioso
    "crochet": [
        "Só mais uma carreirinha...eu prometo",
        "Shh, tô contando os pontos, não me faz errar a conta",
    ],
    "music": [
        "Essa playlist é ótima. Você não tá ouvindo, mas eu tô rs",
        "Fone on, mundo off, produtividade altissíma",
        "Bota um funk ai prá nóis ouvir!",
        "Quero ouvir rock agora, que tal?",
    ],
    "coffee": [
        "Cafézinho imaginário, efeito real",
        "Bebendo café que não existe #performático",
        "Café imaginário, mas tô sentindo o efeito",
    ],
}


class DialogueBank:
    """Sorteia falas evitando repetir as últimas usadas."""

    def __init__(self, memory_size: int = 8):
        self._recent = deque(maxlen=memory_size)

    def get(self, category: str) -> Optional[str]:
        """Retorna uma frase da categoria, evitando as usadas recentemente."""
        options = PHRASES.get(category)
        if not options:
            return None

        # Prefere frases que ainda não saíram; se todas já saíram, libera geral
        fresh = [p for p in options if p not in self._recent]
        pool = fresh if fresh else options

        phrase = random.choice(pool)
        self._recent.append(phrase)
        return phrase

    def status_line(self, days_together: int, total_pets: int, total_feeds: int) -> str:
        """Monta a fala de status - descritiva, nunca uma métrica de cobrança."""
        if days_together <= 0:
            tempo = "A gente se conheceu hoje"
        elif days_together == 1:
            tempo = "1 dia juntos"
        else:
            tempo = f"{days_together} dias juntos"

        return f"{tempo}. {total_pets} carinhos, {total_feeds} lanches. Zero cobranças."
