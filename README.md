# Processamento de Imagens — M2.1 e M2.2 (Python)

Projeto único com `segment` (M2.1) e `analyze` (M2.2), executado por linha de comando. Usa Python, NumPy e OpenCV; não depende de notebook nem de IDE específica.

## 1. Preparação (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m pdi_lab --help
```

Linux/macOS: `python3 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r requirements.txt`, `export PYTHONPATH=src`.

## 2. Imagens

Imagens disponíveis imagens em `images/input/demo_favoravel.png` e `demo_dificuldade.png`

## 3. M2.1 — segmentação

Limiar fixo (pixels cinza > 120 viram 255):
```powershell
$env:PYTHONPATH="src"
python -m pdi_lab --input images/input/demo_favoravel.png --output images/output/demo_favoravel_fixed.png --operation segment --method fixed --threshold 120
```

Otsu, comparável no mesmo caso:
```powershell
python -m pdi_lab --input images/input/demo_favoravel.png --output images/output/demo_favoravel_otsu.png --operation segment --method otsu
```

Repetir ambos para a segunda imagem. O código também aceita `adaptive` (`--block-size 11 --c 2`, bloco ímpar >=3) e `hsv` (`--hsv-lower H S V --hsv-upper H S V`, H 0–179, S/V 0–255). Use `--invert` se o objeto for mais escuro que o fundo; documente a decisão. Para HSV, o padrão de limites cobre quase todo o espaço HSV e só é útil como ponto de partida: defina intervalos específicos para seu objeto.

A máscara PNG é validada para ter mesmo tamanho, um canal e apenas 0/255. O terminal imprime pixels de primeiro plano e proporção.

## 4. M2.2 — componentes e morfologia

Use uma máscara criada no M2.1:
```powershell
python -m pdi_lab --input images/output/demo_favoravel_otsu.png --output results/demo_favoravel --operation analyze --connectivity 8 --min-area 20 --kernel 3 --iterations 1
```

`--output` é um prefixo. São criados `_initial.png`, `_opening.png`, `_final.png`, `_initial.csv`, `_final.csv`, `_labels.png` e `_summary.json`. Sequência padrão: abertura (remove pequenas partículas) seguida de fechamento (preenche pequenas falhas). Elemento estruturante elíptico 3x3, uma iteração. Parâmetros reproduzíveis por argumentos. `--connectivity` aceita 4 ou 8; `--min-area` é opcional (padrão 20 pixels). CSV inicial lista componentes sem filtro (`kept=true` para área >=0); CSV final informa a aplicação do filtro configurado.

## 5. Testes

```powershell
$env:PYTHONPATH="src"
python -m pytest -v
```

## 6. Estrutura

- `src/pdi_lab/`: implementação CLI
- `tests/`: testes automatizados
- `images/input/`: originais/demos
- `images/output/`: máscaras segmentadas
- `results/`: saídas de análise
- `REPORT.md`: relatório-modelo a completar com observações reais
- `AI_USAGE.md`: declaração de uso de IA
- `lab.json`: metadados; preencha seu nome

Não envie `.venv`, `__pycache__` ou `.pytest_cache`.
