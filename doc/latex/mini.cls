\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{mini}[2016/03/01 Praca dyplomowa (MiNI PW)]

% Ustawienie formatu bazowego dokumentu

%\DeclareOption{12pt}{\OptionNotUsed}
%\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ProcessOptions\relax
\LoadClass[a4paper,11pt,twoside,openright]{report}
\RequirePackage{graphicx}

% Ustawienia językowe -- polskie kodowanie znaków

\RequirePackage[utf8]{inputenc}
\RequirePackage[OT4]{fontenc} % TODO OT4 vs T1
\RequirePackage[polish]{babel}
\RequirePackage[OT4]{polski} % TODO OT4 needed?

% Dostosowanie marginesów strony

\textwidth\paperwidth
\advance\textwidth -55mm
\oddsidemargin-1in
\advance\oddsidemargin 30mm
\evensidemargin-1in
\advance\evensidemargin 25mm
\topmargin -1in
\advance\topmargin 2cm
\setlength\textheight{48\baselineskip}
\addtolength\textheight{\topskip}
\marginparwidth15mm

% Można też tak ustawić marginesy -- nie wiem czy któryś sposób jest preferowany
%
%\RequirePackage{geometry}
%\geometry{
%	inner=25mm,
%	outer=25mm,
%	bindingoffset=5mm,
%	top=20mm,
%	bottom=15mm,
%	includeheadfoot
%}

% Font URLi i zawijanie bardzo długich adresów URL

\PassOptionsToPackage{hyphens}{url}
%\RequirePackage[unicode,plainpages=false,hypertexnames=true]{hyperref}
\RequirePackage[unicode]{hyperref}

% Zwykły \href z verbatim font

\newcommand\hreftt[2]{%
	\href{#1}{\texttt{#2}}%
}

%\let\oldhref\href
%\renewcommand{\href}[2]{\oldhref{#1}{#2}}

% Ustawienia wyłączenia podświetlania linków za pomocą kolorowych ramek

%\hypersetup{
%	bookmarksopen,
%	bookmarksopenlevel=1,
%	pdfborder={0 0 0},
%	pdfdisplaydoctitle,
%	pdfpagelayout={SinglePage},
%	pdfstartview={FitH},
%	colorlinks=true
%}

% Listingi kodu

\RequirePackage{listings}
\RequirePackage{subcaption}
\RequirePackage{changepage}
\RequirePackage{xcolor}
\definecolor{green}{rgb}{0,0.6,0}
\definecolor{black}{rgb}{0,0,0}
\definecolor{orange}{rgb}{0.4,0,0}
%\definecolor{purple}{rgb}{0.4,0.6,0}
\lstdefinestyle{customc}{
	numbers=left,
	stepnumber=1,
	numbersep=10pt,
	belowcaptionskip=1\baselineskip,
	breaklines=true,
	frame=l,
%	xleftmargin=\parindent,
	language=C,
	showstringspaces=false,
	basicstyle=\footnotesize\ttfamily,
	keywordstyle=\bfseries\color{green!50!black},
	commentstyle=\itshape\color{green!60!black},
%	identifierstyle=\color{blue!60!black},
	identifierstyle=\color{black},
	stringstyle=\color{orange},
	captionpos=b,
	frame=single
%	frame=top,
%	frame=bottom
}

% Umożliwienie korzystania z polskich liter w listingach kodu

\lstset{
	prebreak=\raisebox{0ex}[0ex][0ex]{\ensuremath{\hookleftarrow}},
	escapechar=@,
	style=customc,
	literate=%
	{ą}{{\k{a}}}1
	{ć}{{\'c}}1
	{ę}{{\k{e}}}1
	{ł}{{\l{}}}1
	{ń}{{\'n}}1
	{ó}{{\'o}}1
	{ś}{{\'s}}1
	{ż}{{\.z}}1
	{ź}{{\'z}}1
	{Ą}{{\k{A}}}1
	{Ć}{{\'C}}1
	{Ę}{{\k{E}}}1
	{Ł}{{\L{}}}1
	{Ń}{{\'N}}1
	{Ó}{{\'O}}1
	{Ś}{{\'S}}1
	{Ż}{{\.Z}}1
	{Ź}{{\'Z}}1
}

% Centrowanie podpisów pod obrazkami, listingami kodu itp.

\RequirePackage[justification=centering]{caption}

% Umożliwienie korzystania z przypisów

\RequirePackage{footnote}
%\RequirePackage{tikz}
%\usetikzlibrary{matrix}

% Włączenie nagłówków na każdej stronie z informacją o numerze strony i tytułem

\RequirePackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
%\fancyhead[RO,LE]{\slshape\rightmark}
%\fancyhead[LO,RE]{\slshape\leftmark}
%\fancyfoot[C]{\thepage}
\fancyhead[RE]{\slshape\leftmark}
\fancyhead[LO]{\slshape\rightmark}
\fancyhead[LE,RO]{\thepage}

\renewcommand{\chaptermark}[1]{\markboth{\thechapter.\enspace#1}{}}
\renewcommand{\sectionmark}[1]{\markright{\thesection.\enspace#1}}
\def\cleardoublepage{\clearpage\if@twoside
	\ifodd\c@page\else\hbox{}\thispagestyle{empty}\newpage
	\if@twocolumn\hbox{}\newpage\fi\fi\fi}
\renewcommand{\@seccntformat}[1]{\csname the#1\endcsname.\enspace}
\renewcommand{\numberline}[1]{\hb@xt@\@tempdima{#1.\hfil}}
\RequirePackage[parfill]{parskip}[2001/04/09]
\RequirePackage{setspace}
\frenchspacing
\clubpenalty=10000
\widowpenalty=10000
\brokenpenalty=10000

% Ustawienia słownika pojęć (glossaries)

\RequirePackage[nomain,acronym,xindy={language=polish,codepage=utf8},nonumberlist]{glossaries}
%\RequirePackage{glossary-mcols} % for 2 columns \printglossary[style=mcolindex]
%\renewcommand*{\glstextformat}{\texttt} % font dla odwołań \gls
\renewcommand{\glsnamefont}[1]{\textbf{#1}} % font dla haseł w słowniku
\renewcommand*{\glspostdescription}{}
\newglossarystyle{labeling}{%
	\renewenvironment{theglossary}%
		{\begin{longtable}{p{.2\linewidth}p{1.5\glsdescwidth}}}%
		{\end{longtable}}%
	\renewcommand*{\glspostdescription}{.\\}%
	\renewcommand*{\glossaryheader}{}%
	\renewcommand*{\glsgroupheading}[1]{}%
	\renewcommand*{\glossaryentryfield}[5]{%
		\glstarget{##1}{##2} & ##3\glspostdescription\space ##5\\}%
	\renewcommand*{\glossarysubentryfield}[6]{%
		& \glstarget{##2}{\strut}##4\glspostdescription\space ##6\\}%
	\renewcommand*{\glsgroupskip}{}%
}

\makeglossaries

% Ustawienia polskiego formatowania cytowanej bibliografii

\RequirePackage{csquotes}
\DeclareQuoteStyle[quotes]{polish}
	{\quotedblbase}
	{\textquotedblright}
	[0.05em]
	{\quotesinglbase}
	{\fixligatures\textquoteright}
\DeclareQuoteAlias[quotes]{polish}{polish}
\DeclareQuoteOption{polish}

\RequirePackage[
	style=numeric,
	backend=biber,
	sorting=none,
	backref=true]{biblatex}
\addbibresource{bibliography.bib}

% Paczki dla matematycznych formuł

%\RequirePackage{mathtools} % do not use old amsmath package
%\RequirePackage{amsthm}
%\RequirePackage{amsfonts}
%\RequirePackage{amssymb}

% Ustawienie wcięć na początku każdego akapitu

%\RequirePackage{indentfirst}
%\setlength{\parindent}{1cm}

\RequirePackage{array}
\RequirePackage{enumitem}
\RequirePackage{wrapfig}
\def\@schapter#1{
	\phantomsection\addcontentsline{toc}{chapter}{#1}
	\markboth{#1}{#1}\@makeschapterhead{#1}\@afterheading}

% Usunięcie ze spisu treści odwołania do spisu treści

\renewcommand{\tableofcontents}{
	\if@openright\cleardoublepage\else\clearpage\fi\thispagestyle{plain}
	\pdfbookmark[0]{\contentsname}{tableofcontents}
	\@makeschapterhead{\contentsname}\@afterheading
	\@mkboth{\MakeUppercase\contentsname}{\MakeUppercase\contentsname}
	\@starttoc{toc}}

% Stałe / zmienne

\def\title#1{\gdef\@title{#1}\hypersetup{pdftitle={#1}}}
\def\@title{\@latex@error{No polish title given}\@ehc}
\def\titleaux#1{\gdef\@titleaux{#1}}
\def\@titleaux{\@latex@error{No english title given}\@ehc}
\def\author#1{\gdef\@author{#1}}
\def\@author{\@latex@error{No author given}\@ehc}
\def\supervisor#1{\gdef\@supervisor{#1}}
\def\@supervisor{\@latex@error{No supervisor given}\@ehc}
\def\discipline#1{\gdef\@discipline{#1}}
\def\@discipline{\@latex@error{No discipline given}\@ehc}
\def\monthyear#1{\gdef\@monthyear{#1}}
\def\@monthyear{\@latex@error{No month and year given}\@ehc}
%\def\date#1{\gdef\@date{#1}}
%\def\@date{\@latex@error{No date given}\@ehc}
\def\album#1{\gdef\@album{#1}}
\def\@album{\@latex@error{No album number given}\@ehc}
\def\@university{Politechnika Warszawska}
\def\@faculty{Wydzia{\l} Matematyki i Nauk Informacyjnych}
\def\@authorcap{Autor}
\def\@supervisorcap{Promotor}
\def\@location{Warszawa}
\def\@authorsig{podpis autora}
\def\@supervisorsig{podpis promotora}
\def\@titlepagecap{Strona tytu{\l}owa}
\def\@academicyear{2016/2017}
%\def\@statementcap{O{\'s}wiadczenie}
%\def\@definition{Definicja}
%\def\@corollary{Wniosek}
%\def\@remark{Uwaga}
%\def\@example{Przyk{\l}ad}

% Załączniki

\RequirePackage[toc,page]{appendix}

\def\zalaczniki{Załączniki}
\renewcommand{\appendixtocname}{\zalaczniki}
\renewcommand{\appendixpagename}{\zalaczniki}

% Wyświetlanie drzewa katalogów

\usepackage{dirtree}

% Strona tytułowa

\renewcommand{\maketitle}{
	\pdfbookmark[0]{\@titlepagecap}{titlepage}
	\begin{titlepage}
	\newcommand{\HRule}{\rule{\linewidth}{0.5mm}}
		\center
		\begin{minipage}{2.5cm}
			\includegraphics[width=2.25cm]{img/pw}
		\end{minipage}
		\hfill
		\begin{minipage}{100mm}
			\begin{center}
				\textsc{\LARGE\@university\\\vspace{1mm}\large\@faculty}
			\end{center}
		\end{minipage}
		\hfill
		\begin{minipage}{2.5cm}
			\begin{flushright}
					\includegraphics[width=2.25cm]{img/mini}
			\end{flushright}
		\end{minipage}\par
		\vspace{3cm}
		{
			\textsc{\Large Praca dyplomowa magisterska na kierunku \@discipline}\\[0.5cm]
			\textsc{\large Rok akademicki \@academicyear}\\[1.8cm]
		\par}
		\HRule\\[1.5cm]
		\begin{minipage}[t]{0.95\textwidth}
		\begin{spacing}{2.0}
			\center
			\textbf{\LARGE\@title}
		\end{spacing}
		\end{minipage}\\[0.5cm]
		\HRule\\[2cm]
	\begin{minipage}[t]{0.4\textwidth}
		\begin{flushleft}\large
			\textsc{\@authorcap:}\\[3mm]
			\@author
		\end{flushleft}
	\end{minipage}
	\begin{minipage}[t]{0.4\textwidth}
		\begin{flushright}\large
			\textsc{\@supervisorcap:}\\[3mm]
			\@supervisor\\[1cm]
		\end{flushright}
	\end{minipage}
	\vfill
	%\hspace{.7\textwidth}
	%\begin{minipage}[t][70mm]{.4\textwidth}
	%	\textsc{\large\@authorcap:}\\\@author\par
	%	\vspace{7mm}
	%	\textsc{\large\@supervisorcap:}\\\@supervisor
	%\end{minipage}
	\begin{center}
		\textsc{\large\@location, \@monthyear}
	\end{center}
	\vspace{5mm}
	\clearpage
	\thispagestyle{empty}
	\null\vfill
	\begin{minipage}{50mm}
		\begin{center}
			..............................................\\
			\vspace{1mm}
			\@supervisorsig
		\end{center}
	\end{minipage}
	\hfill
	\begin{minipage}{50mm}
		\begin{center}
			..............................................\\
			\vspace{1mm}
			\@authorsig
		\end{center}
	\end{minipage}
	\end{titlepage}}
\endinput
