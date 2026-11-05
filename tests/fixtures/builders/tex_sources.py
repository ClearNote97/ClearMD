"""The LaTeX sources of feature 002."""

PAPER_TEX = r"""\documentclass{article}
\usepackage[spanish]{babel}
\usepackage{graphicx,hyperref,listings,amsmath}
\title{Un art\'iculo de prueba}
\author{Ana P\'erez}
\date{2026}
\begin{document}
\maketitle
\begin{abstract}
Resumen breve con $x^2$.
\end{abstract}
\section{Introducci\'on}
Texto con \textbf{negrita}, \textit{it\'alica}, \emph{\'enfasis}, \texttt{c\'odigo} y
\underline{subrayado}. Marcador: fixture-tex-paper.
Ver \cite{knuth84,lamport94} y la ecuaci\'on~\eqref{eq:pit}.\footnote{Una nota al pie.}
\subsection{Listas}
\begin{itemize}
  \item uno
  \item dos
  \begin{enumerate}
    \item anidado
  \end{enumerate}
\end{itemize}
\begin{description}
  \item[T\'ermino] Su definici\'on.
\end{description}
\subsection{Matem\'aticas}
En l\'inea $E=mc^2$ y \(a+b\) y $\alpha_{i}~\text{texto}$.
\[ \int_0^1 x\,dx \]
\begin{equation}\label{eq:pit} a^2+b^2=c^2 \end{equation}
\begin{align} x &= 1 \\ y &= 2 \end{align}
\subsection{C\'odigo y citas}
\begin{lstlisting}[language=Python]
print("hola $no math$ \section{no}")
\end{lstlisting}
El comando \verb|\foo| en l\'inea.
\begin{quote}Una cita.\end{quote}
\href{https://example.org}{un enlace} y \url{https://example.org/b} -- rango --- raya ``comillas''.
\subsection{Tablas y figuras}
\begin{table}\centering
\begin{tabular}{|l|c|}\hline
A & B \\ \hline
1 & $x$ \\ \hline
\end{tabular}
\caption{Una tabla}
\end{table}
\begin{figure}\centering
\includegraphics[width=0.5\textwidth]{img/plot}
\caption{Un gr\'afico}
\end{figure}
\newpage
% un comentario que desaparece
\end{document}
"""

UNKNOWN_TEX = r"""\documentclass{article}
\begin{document}
\section{Desconocidos}
Texto \customcommand{x} y \otherthing.
\begin{weirdenv}dentro\end{weirdenv}
\end{document}
"""

MULTICOLUMN_TEX = r"""\documentclass{article}
\begin{document}
\begin{tabular}{lcc}
\multicolumn{2}{c}{Encabezado} & C \\
1 & 2 & 3 \\
\end{tabular}
\end{document}
"""

MALFORMED_TEX = r"""\documentclass{article}
\begin{document}
\section{Abierto
Texto despu\'es de un grupo sin cerrar, fixture-tex-malformed.
\end{itemize}
\end{document}
"""

LATIN1_BODY = (
    "\\section{Introducción}\nCañón, acción y ñandú: fixture-tex-latin1.\n\\end{document}\n"
)
LATIN1_DECLARED = (
    "\\documentclass{article}\n\\usepackage[latin1]{inputenc}\n\\begin{document}\n" + LATIN1_BODY
)
LATIN1_UNDECLARED = "\\documentclass{article}\n\\begin{document}\n" + LATIN1_BODY

THESIS_MAIN = r"""\documentclass{report}
\usepackage[spanish]{babel}
\input{macros}
\graphicspath{{img/}}
\title{Una tesis}
\author{Autor}
\begin{document}
\maketitle
\input{chapters/ch1}
\include{chapters/ch2}
\end{document}
"""
THESIS_MACROS = r"""\newcommand{\R}{\mathbb{R}}
\newcommand{\norm}[1]{\left\lVert #1 \right\rVert}
\newcommand{\pair}[2][0]{(#1, #2)}
\DeclareMathOperator{\argmax}{arg\,max}
\def\ClearMD{ClearMD}
"""
THESIS_CH1 = r"""\chapter{Primer cap\'itulo}
Sea $x \in \R$ con $\norm{x} \le 1$ y $\pair{a}$, $\pair[b]{c}$. Herramienta: \ClearMD{}.
Marcador: fixture-tex-ch1.
\begin{figure}\includegraphics{plot}\caption{Desde graphicspath}\end{figure}
"""
THESIS_CH2 = r"""\chapter{Segundo cap\'itulo}
$\argmax_{\theta} f(\theta)$. Marcador: fixture-tex-ch2.
\input{chapters/sections/deeper}
"""
THESIS_DEEPER = r"""\section{M\'as hondo}
Marcador: fixture-tex-deeper.
"""


def _document(body: str) -> str:
    return f"\\documentclass{{article}}\\begin{{document}}{body}\\end{{document}}\n"


def _bomb_name(level: int) -> str:
    """Letters only: in LaTeX a digit ends a macro name (\\mac0 is \\mac followed by 0)."""
    return "\\bomb" + chr(ord("a") + level // 26) + chr(ord("a") + level % 26)


BOMB_LEVELS = 40
HOSTILE = {
    "absolute.tex": _document("\\input{/etc/passwd}"),
    "parent.tex": _document("\\input{../paper}"),
    "not_tex.tex": _document("\\input{data.csv}"),
    "missing.tex": _document("\\input{nowhere}"),
    "cycle_a.tex": "A \\input{cycle_b}\n",
    "cycle_b.tex": "B \\input{cycle_a}\n",
    "recursive_macro.tex": (
        "\\documentclass{article}\\newcommand{\\loop}{x\\loop}"
        "\\begin{document}Antes $\\loop$ despues\\end{document}\n"
    ),
    # 2**40 copies of "x" if nothing stopped it.
    "exponential_macro.tex": (
        "\\documentclass{article}"
        + "".join(
            f"\\def{_bomb_name(i)}{{{_bomb_name(i + 1)}{_bomb_name(i + 1)}}}"
            for i in range(BOMB_LEVELS)
        )
        + f"\\def{_bomb_name(BOMB_LEVELS)}{{x}}"
        + f"\\begin{{document}}${_bomb_name(0)}$\\end{{document}}\n"
    ),
    "data.csv": "a,b\n1,2\n",
}
for level in range(10):
    following = f"\\input{{deep{level + 1}}}" if level < 9 else "fondo"
    HOSTILE[f"deep{level}.tex"] = f"nivel {level} {following}\n"
