# Assets

Onde os sprites entram. Enquanto não houver arte aqui, o Foqui desenha um
placeholder em código (`AnimationManager._create_placeholder_frame`).

```
assets/
  pets/<tipo>/         frog, rat, cat, robot
  icons/               tray_<tipo>.png
  ui/                  elementos de interface
  sounds/              gerado automaticamente na primeira execução
```

## Sprites de um pet

Cada animação pode ser entregue de duas formas dentro de `assets/pets/<tipo>/`:

1. **Sprite sheet horizontal**: `idle_breathe.png` com os frames lado a lado.
2. **Frames soltos**: `idle_breathe_0.png`, `idle_breathe_1.png`, ...

Frame base: 64x64 px, fundo transparente.

Animações esperadas e quantidade de frames (ver `src/animation.py`):

| Animação | Frames | Loop |
|---|---|---|
| `idle_breathe` | 4 | sim |
| `idle_blink` | 3 | não |
| `idle_look` | 6 | não |
| `walk_right` | 8 | sim |
| `walk_left` | 8 | sim |
| `sleep_enter` | 4 | não |
| `sleep_loop` | 4 | sim |
| `sleep_exit` | 4 | não |
| `yawn` | 6 | não |
| `eat` | 8 | não |
| `pet_reaction` | 6 | não |
| `happy_jump` | 6 | não |
| `curious` | 4 | não |

Faltou alguma? O Foqui usa o placeholder só naquela animação, sem quebrar.
