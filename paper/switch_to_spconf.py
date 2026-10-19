#!/usr/bin/env python3
"""
Gera main_spconf.tex a partir de main.tex, trocando o preâmbulo IEEEtran
pelo template oficial do ICASSP (spconf.sty + IEEEbib.bst).

Por que existe: o ICASSP NÃO aceita IEEEtran. O layout é parecido o
suficiente para enganar, e diferente o suficiente para o paper voltar.
O corpo do texto é idêntico nos dois -- só o preâmbulo muda -- então esse
script roda de novo sempre que você editar main.tex, sem retrabalho.

Antes de compilar, coloque na pasta (baixe do paper kit do ICASSP):
    spconf.sty
    IEEEbib.bst

Uso:
    python switch_to_spconf.py
    latexmk -pdf main_spconf.tex
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "main.tex"
DST = HERE / "main_spconf.tex"

# --------------------------------------------------------------- preâmbulo
# spconf carrega o essencial; o resto continua vindo dos \usepackage abaixo.
NEW_CLASS = r"""\documentclass{article}
\usepackage{spconf}                                %<<TEMPLATE OFICIAL>>"""

# --------------------------------------------------------------- autores
# spconf usa \name{} e \address{} -- \author{} + \IEEEauthorblock* não existem.
# Vários autores: separe com \qquad dentro de \name{}. Afiliações diferentes
# pedem \twoauthors{...}{...}{...}{...} -- veja o Template.tex do kit.
NEW_AUTHOR = r"""\name{Cândido de Lucena Filho\thanks{\TODO{coautores, e-mail e a linha de fomento (CAPES / FAPESP / CNPq) entram aqui}}}
\address{Escola Politécnica, Universidade de São Paulo, São Paulo, Brazil}"""

AUTHOR_BLOCK = re.compile(
    r"\\author\{\\IEEEauthorblockN\{.*?\}\}\s*(?=\n\\begin\{document\})",
    re.DOTALL,
)


def convert(text: str) -> str:
    n = {"class": 0, "author": 0, "ninept": 0, "bib": 0}

    # 1. classe do documento
    text, k = re.subn(
        r"^\\documentclass\[[^\]]*\]\{IEEEtran\}.*$",
        NEW_CLASS.replace("\\", "\\\\"),
        text,
        count=1,
        flags=re.MULTILINE,
    )
    n["class"] = k

    # 2. bloco de autores
    text, k = AUTHOR_BLOCK.subn(NEW_AUTHOR.replace("\\", "\\\\") + "\n", text)
    n["author"] = k

    # 3. \ninept logo depois de \begin{document} -- é o corpo 9pt do ICASSP
    text, k = re.subn(
        r"(\\begin\{document\}\n)(\\maketitle)",
        r"\1\\ninept\n\2",
        text,
        count=1,
    )
    n["ninept"] = k

    # 4. estilo bibliográfico
    text, k = re.subn(
        r"\\bibliographystyle\{IEEEtran\}.*",
        r"\\bibliographystyle{IEEEbib}",
        text,
        count=1,
    )
    n["bib"] = k

    # 5. cabeçalho do arquivo gerado
    banner = (
        "% =====================================================================\n"
        "%  GERADO POR switch_to_spconf.py -- NÃO EDITE ESTE ARQUIVO À MÃO.\n"
        "%  Edite main.tex e rode:  python switch_to_spconf.py\n"
        "%\n"
        "%  Precisa de spconf.sty e IEEEbib.bst na pasta. Baixe do paper kit:\n"
        "%  https://cmsworkshops.com/ICASSP2026/papers/paper_kit.php\n"
        "% =====================================================================\n"
    )
    return banner + text, n


def main() -> int:
    if not SRC.exists():
        print(f"não achei {SRC}", file=sys.stderr)
        return 1

    out, n = convert(SRC.read_text(encoding="utf-8"))

    missing = [k for k, v in n.items() if v == 0]
    if missing:
        print(
            "AVISO: estas trocas não pegaram -> " + ", ".join(missing) +
            "\n  main.tex mudou de forma? Confira à mão antes de submeter.",
            file=sys.stderr,
        )

    DST.write_text(out, encoding="utf-8")
    print(f"escrevi {DST.name}")

    for f in ("spconf.sty", "IEEEbib.bst"):
        if not (HERE / f).exists():
            print(f"  falta {f} -- baixe do paper kit antes de compilar")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
