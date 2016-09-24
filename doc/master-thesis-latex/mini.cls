\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{mini}[2016/03/01 Praca dyplomowa (MiNI PW)]

\RequirePackage{ifthen}
%------------------------------------------------------------------------------%
%\DeclareOption{12pt}{\OptionNotUsed}
%\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ProcessOptions\relax
\LoadClass[a4paper,11pt,twoside,onecolumn,openright]{report}
%------------------------------------------------------------------------------%
\RequirePackage[utf8]{inputenc}
%------------------------------------------------------------------------------%
\RequirePackage{graphicx}
%------------------------------------------------------------------------------%
\RequirePackage{alltt}
%------------------------------------------------------------------------------%
\RequirePackage{blkarray}
%------------------------------------------------------------------------------%
\RequirePackage{multirow}
%------------------------------------------------------------------------------%
\RequirePackage{floatrow}
\DeclareFloatVCode{ruleabove}
{\par\rule{\hsize}{1pt}\vskip5pt\par}
%\DeclareFloatVCode{rulebelow} % podkreslenia m.in. pod tabelami
%{\par\vskip -7pt\rule{\hsize}{1pt}\par}
\DeclareFloatVCode{programrulebelow}
{\par\vskip 5pt\rule{\hsize}{1pt}\par}

% Przyklad programu:
%\floatsetup{capposition=bottom,floatrowsep=qquad,valign=c,heightadjust=object,margins=centering,precode=ruleabove,midcode=rulebelow}
\newfloat{program}{thp}{lop}[chapter]
\floatname{program}{Przyk{\l}ad}
\floatsetup[program]{style=ruled,capposition=top,heightadjust=object,margins=raggedleft,objectset=centering,postcode=programrulebelow}
\captionsetup{justification=justified,singlelinecheck=false}

% Przyklad matematyczny:
%\floatsetup{capposition=bottom,floatrowsep=qquad,valign=c,heightadjust=object,margins=centering,precode=ruleabove,midcode=rulebelow}
\newfloat{przyklad}{thp}{lop}[chapter]
\floatname{przyklad}{Przyk{\l}ad}
\floatsetup[przyklad]{style=ruled,capposition=top,heightadjust=object,margins=centering,objectset=centering,postcode=programrulebelow}
%------------------------------------------------------------------------------%
\PassOptionsToPackage{hyphens}{url} % zawijanie bardzo dlugich adresow URL
\RequirePackage[unicode]{hyperref}
\hypersetup{
	bookmarksopen,
	bookmarksopenlevel=1,
	pdfborder={0 0 0},
	pdfdisplaydoctitle,
	pdfpagelayout={SinglePage},
	pdfstartview={FitH}
}
%------------------------------------------------------------------------------%
\RequirePackage{listings}
%------------------------------------------------------------------------------%
\RequirePackage{mathtools}
%------------------------------------------------------------------------------%
\RequirePackage{subcaption}
%------------------------------------------------------------------------------%
\RequirePackage{changepage}
%------------------------------------------------------------------------------%
\RequirePackage[usenames,dvipsnames]{color}
\RequirePackage{xcolor}
\definecolor{green}{rgb}{0,0.6,0}
\definecolor{black}{rgb}{0,0,0}
\definecolor{orange}{rgb}{0.4,0,0}
\definecolor{purple}{rgb}{0.4,0.6,0}
\lstdefinestyle{customc}{
	numbers=left,
	stepnumber=1,
	numbersep=10pt,
	belowcaptionskip=1\baselineskip,
	breaklines=true,
	frame=l,
	xleftmargin=\parindent,
	language=C,
	showstringspaces=false,
	basicstyle=\footnotesize\ttfamily,
	keywordstyle=\bfseries\color{green!50!black},
	commentstyle=\itshape\color{green!60!black},
	identifierstyle=\color{blue},
	stringstyle=\color{orange},
	captionpos=b,
	frame=top,
	frame=bottom
}
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
%------------------------------------------------------------------------------%
\RequirePackage{footnote}
\RequirePackage{geometry}
\geometry{
	inner=25mm,
	outer=25mm,
	bindingoffset=5mm,
	top=20mm,
	bottom=15mm,
	includeheadfoot
}
%------------------------------------------------------------------------------%
\RequirePackage{tikz}
\usetikzlibrary{matrix}
%------------------------------------------------------------------------------%
\RequirePackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
%\fancyhead[RO,LE]{\slshape\rightmark}
%\fancyhead[LO,RE]{\slshape\leftmark}
%\fancyfoot[C]{\thepage}
\fancyhead[RE]{\slshape\leftmark}
\fancyhead[LO]{\slshape\rightmark}
\fancyhead[LE,RO]{\thepage}
%------------------------------------------------------------------------------%
\renewcommand{\chaptermark}[1]{\markboth{\thechapter.\enspace#1}{}}
\renewcommand{\sectionmark}[1]{\markright{\thesection.\enspace#1}}
%------------------------------------------------------------------------------%
\def\cleardoublepage{\clearpage\if@twoside
\ifodd\c@page\else\hbox{}\thispagestyle{empty}\newpage
\if@twocolumn\hbox{}\newpage\fi\fi\fi}
%------------------------------------------------------------------------------%
\renewcommand{\@seccntformat}[1]{\csname the#1\endcsname.\enspace}
\renewcommand{\numberline}[1]{\hb@xt@\@tempdima{#1.\hfil}}
%------------------------------------------------------------------------------%
\RequirePackage[parfill]{parskip}[2001/04/09]
\RequirePackage{setspace}
\frenchspacing
%------------------------------------------------------------------------------%
\clubpenalty=10000
\widowpenalty=10000
\brokenpenalty=10000
%------------------------------------------------------------------------------%
\RequirePackage[nomain,acronym,xindy,nonumberlist]{glossaries}
\renewcommand{\acronymname}{S{\l}ownik}
\renewcommand*{\glstextformat}{\textit}
\renewcommand{\glsnamefont}[1]{\textbf{#1}}
%\renewcommand*{\glspostdescription}{}

\newglossarystyle{clong}{%
	\renewenvironment{theglossary}%
		{\begin{longtable}{p{.25\linewidth}p{1.45\glsdescwidth}}}%
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

\usepackage[xindy]{imakeidx}
\makeindex
%------------------------------------------------------------------------------%
\RequirePackage{amsmath}
\RequirePackage{amsthm}
\RequirePackage{amsfonts}
\RequirePackage{amssymb}
\RequirePackage{indentfirst}
\setlength{\parindent}{1cm}
\RequirePackage{array}
\RequirePackage{enumitem}
%------------------------------------------------------------------------------%
\RequirePackage[OT4]{polski}
%------------------------------------------------------------------------------%
\RequirePackage{wrapfig}
%------------------------------------------------------------------------------%
\def\@schapter#1{
\phantomsection\addcontentsline{toc}{chapter}{#1}
\markboth{#1}{#1}\@makeschapterhead{#1}\@afterheading}
%------------------------------------------------------------------------------%
\renewcommand{\tableofcontents}{
\if@openright\cleardoublepage\else\clearpage\fi\thispagestyle{plain}
\pdfbookmark[0]{\contentsname}{tableofcontents}
\@makeschapterhead{\contentsname}\@afterheading
\@mkboth{\MakeUppercase\contentsname}{\MakeUppercase\contentsname}
\@starttoc{toc}}
%------------------------------------------------------------------------------%
\def\title#1{\gdef\@title{#1}\hypersetup{pdftitle={#1}}}
\def\@title{\@latex@error{No title given}\@ehc}
\def\titleaux#1{\gdef\@titleaux{#1}}
\def\@titleaux{\@latex@error{No polish title given}\@ehc}
\def\author#1{\gdef\@author{#1}}
\def\@author{\@latex@error{No author given}\@ehc}
\def\supervisor#1{\gdef\@supervisor{#1}}
\def\@supervisor{\@latex@error{No supervisor given}\@ehc}
\def\discipline#1{\gdef\@discipline{#1}}
\def\@discipline{\@latex@error{No discipline given}\@ehc}
\def\monthyear#1{\gdef\@monthyear{#1}}
\def\@monthyear{\@latex@error{No month and year given}\@ehc}
\def\date#1{\gdef\@date{#1}}
\def\@date{\@latex@error{No date given}\@ehc}
\def\album#1{\gdef\@album{#1}}
\def\@album{\@latex@error{No album number given}\@ehc}
%------------------------------------------------------------------------------%
\def\@university{Politechnika Warszawska}
\def\@faculty{Wydzia{\l} Matematyki i Nauk Informacyjnych}
\def\@authorcap{Autor}
\def\@supervisorcap{Promotor}
\def\@location{Warszawa}
\def\@authorsig{podpis Autora}
\def\@supervisorsig{podpis Promotora}
\def\@titlepagecap{Strona tytu{\l}owa}
\def\@statementcap{O{\'s}wiadczenie}
%------------------------------------------------------------------------------%
\def\@definition{Definicja}
\def\@corollary{Wniosek}
\def\@remark{Uwaga}
\def\@example{Przyk{\l}ad}
%------------------------------------------------------------------------------%
\def\bibname{Literatura}
%------------------------------------------------------------------------------%
\renewcommand{\maketitle}{
\pdfbookmark[0]{\@titlepagecap}{titlepage}
\begin{titlepage}
\begin{center}
	\begin{minipage}{25mm}
		\includegraphics[scale=0.75]{img/pw}
	\end{minipage}
	\hfill
	\begin{minipage}{100mm}
		\begin{center}
			\textsc{\Large\@university\\\vspace{1mm}\large\@faculty}
		\end{center}
	\end{minipage}
	\hfill
	\begin{minipage}{25mm}
		\begin{flushright}
				\includegraphics[scale=0.75]{img/mini}
		\end{flushright}
	\end{minipage}\par
	\vspace{30mm}
	{\large
		\MakeUppercase{Praca dyplomowa magisterska}\\
		\MakeUppercase{na kierunku \@discipline}
	\par}
	\vfill
	\begin{spacing}{1.3}
		\textbf{\Large\MakeUppercase{\@title}}
	\end{spacing}
	\vfill
\end{center}
\hspace{.7\textwidth}
\begin{minipage}[t][70mm]{.5\textwidth}
	\textsc{\large\@authorcap:}\\\@author\par
	\vspace{7mm}
	\textsc{\large\@supervisorcap:}\\\@supervisor
\end{minipage}
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
%------------------------------------------------------------------------------%
\newcommand{\matindex}[1]{\mbox{\scriptsize#1}}% Matrix index
%------------------------------------------------------------------------------%
\newcommand{\makestatement}{
\cleardoublepage
\thispagestyle{empty}
\pdfbookmark[0]{\@statementcap}{statement}
\@author\hfill Warszawa, \@date\\
Nr albumu \@album
\par\vspace{25mm}
\begin{center}
	{\Large O{\'s}wiadczenie}
\end{center}
\par\vspace{15mm}
Oświadczam, że pracę magisterską pod tytułem ,,\@title'', której promotorem jest \@supervisor, wykonałem samodzielnie, co poświadczam własnoręcznym podpisem.
\vspace{15mm}
\begin{flushright}
\begin{minipage}{50mm}
		\begin{center}
			..............................................\\
			\vspace{1mm}
			\@author
		\end{center}
	\end{minipage}
\end{flushright}}
%------------------------------------------------------------------------------%
\endinput
