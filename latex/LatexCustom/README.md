# LatexCustom

> [!WARNING]
> work in progress

Personal Latex Template with some basic implementations of [formatting-commands](#-formatting-commands) to copy & paste.
For hyphenation search `main.tex` for `hyphenation` and edit accordingly
Uses Biblatex with biber for citation

## Usage

Here's *one*  way to use this repository:

### Formatting commands {#formatting-commands}

From `./content/01-introduction.tex` you can *copy & paste* any formatting-command you need.
They include:

- bold, italic, underline
- figures (single, multiple)
- tables (aligned, longer paragraphs)
- lists (unordered, numbered)
- sourcecode
- citations
- footnotes
- glossary
- acronyms

### Customization

You might want to customize certain things:

in `./ads/titlepage.tex` (order of appearance)

- `\textbf{Awesome Title}`
- `%Thesis Subtitle`
- `\textbf{Author}`
- and of course replace the *placeholder text*

in `./main.tex` (order of appearance)

- Margins of the document:

```latex
\usepackage[
  left=2cm,
  right=2cm,
  top=2cm,
  bottom=2cm
]{geometry}
```

- `\usepackage[ngerman]{babel} % Change hyphenation rules`
- Rounding behaviour of floats:

```latex
\sisetup{
  round-mode          = places, % Rounds numbers
  round-precision     = 2, % to 2 places
} % table cell value rounding
```

- Citation behaviour

```latex
% BibLaTeX Setup
% ---
\usepackage[
    backend=biber,          % Use biber instead of bibtex
    style=ieee,             % IEEE style (equivalent to IEEEtran)
    % ...
```

- `\setcounter{tocdepth}{3} % show subsections in toc`
- Code formatting (excerpt)

```latex
% General setup for the package
\lstset{
    language=Go,
    % ...
```

### Compile

You *can* use the [`latexcompile.sh`](./latexcompile.sh) script, it just does:

```bash
pdflatex main.tex && biber main && makeglossaries main && pdflatex main.tex && pdflatex main.tex
```

I'm sure there's a better workflow, but for now I just

```bash
./latexcompile.sh && <some-browser> main.pdf
```

to view the file.

## Dependencies

Make sure to to have the following LaTeX packages and tools installed:

- `texlive-basic`
- `texlive-bibtexextra`
- `texlive-fontsextra`
- `texlive-german`
- `texlive-latexextra`
- `texlive-mathscience`
- `texlive-plaingeneric`
- `biber`

