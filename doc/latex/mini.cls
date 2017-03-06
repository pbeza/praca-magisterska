\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{mini}[2016/03/01 Praca dyplomowa (MiNI PW)]

% Ustawienie formatu bazowego dokumentu

%\DeclareOption{12pt}{\OptionNotUsed}
%\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ProcessOptions\relax
\LoadClass[a4paper,11pt,twoside,openright]{report}
\RequirePackage{graphicx}

% Ustawienia językowe (polskie kodowanie znaków)

\RequirePackage[utf8]{inputenc} % inputenc package ignored with utf8 based engines
\RequirePackage[OT4]{fontenc} % TODO OT4 vs T1
\RequirePackage[english,main=polish]{babel}
\let\lll\undefined % fix przed załadowaniem amssymb (konflikt \lll)
\RequirePackage[OT4]{polski} % TODO OT4 needed?

% Zaimportowanie czcionek wymaganych przez wymagania Rektora

\RequirePackage{fontspec}
\newfontfamily{\adagiolight}[
	Path = fonts/,
	UprightFont = adagio_slab-light-webfont,
	ItalicFont = adagio_slab-light_italic-webfont
]{Adagio_Slab}
\newfontfamily{\adagioregular}[
	Path=fonts/,
	UprightFont=adagio_slab-regular-webfont,
	ItalicFont=adagio_slab-regular_italic-webfont
]{Adagio_Slab}
\newfontfamily{\adagioregularmorespace}[
	Path=fonts/,
	UprightFont=adagio_slab-regular-webfont,
	ItalicFont=adagio_slab-regular_italic-webfont,
	WordSpace={3}
]{Adagio_Slab}
%\newfontfamily\arial{Arial} % pakiet ttf-mscorefonts-installer
%\setmainfont[Mapping=tex-text]{Arial}
%\setmainfont{Linux Libertine O}
\setmainfont{Latin Modern Roman} % komenda bash: fc-list | grep ".otf"

% Przedefiniowanie \emph żeby zawsze było pochylone

\let\emph\relax % there's no \RedeclareTextFontCommand
\DeclareTextFontCommand{\emph}{\itshape}

% Fake'owe font Small Caps dla Adagio_Slab (wymagane na stronie tytułowej)
% http://tex.stackexchange.com/questions/55664/fake-small-caps-with-xetex-fontspec
%
\newlength\fake@f
\newlength\fake@c
\def\fakesc#1{%
	\begingroup%
	\xdef\fake@name{\csname\curr@fontshape/\f@size\endcsname}%
	\fontsize{\fontdimen8\fake@name}{\baselineskip}\selectfont%
	\MakeUppercase{#1}%
	\endgroup%
}

% Dostosowanie marginesów strony
% Patrz: https://www.tug.org/TUGboat/tb09-1/tb20mcpherson.pdf
%
%\textwidth\paperwidth
%\advance\textwidth -55mm
%\oddsidemargin-1in
%\advance\oddsidemargin 30mm
%\evensidemargin-1in
%\advance\evensidemargin 25mm
%\topmargin -1in
%\advance\topmargin 2cm
%\setlength\textheight{48\baselineskip}
%\addtolength\textheight{\topskip}
%\marginparwidth15mm

% Można też tak ustawić marginesy -- nie wiem czy któryś sposób jest preferowany

\RequirePackage[
	headheight=15pt, % http://tex.stackexchange.com/questions/85178/increase-height-of-fancyhdr-header
	inner=25mm,
	outer=25mm,
	bindingoffset=5mm,
	top=20mm,
	bottom=15mm,
	includeheadfoot
%	showframe
]{geometry}

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
%	belowcaptionskip=0.1\baselineskip,
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

% Ładne kolorowanie listingów YAML
% http://tex.stackexchange.com/questions/152829/how-can-i-highlight-yaml-code-in-a-pretty-way-with-listings
%
%\newcommand\YAMLcolonstyle{\color{red}\mdseries}
%\newcommand\YAMLkeystyle{\color{black}\bfseries}
%\newcommand\YAMLvaluestyle{\color{blue}\mdseries}
%
%% here is a macro expanding to the name of the language
%% (handy if you decide to change it further down the road)
%\newcommand\language@yaml{yaml}
%
%\expandafter\expandafter\expandafter\lstdefinelanguage
%\expandafter{\language@yaml}
%{
%	keywords={true,false,null,y,n},
%	keywordstyle=\color{darkgray}\bfseries,
%	basicstyle=\YAMLkeystyle,                                 % assuming a key comes first
%	sensitive=false,
%	comment=[l]{\#},
%	morecomment=[s]{/*}{*/},
%	commentstyle=\color{purple}\ttfamily,
%	stringstyle=\YAMLvaluestyle\ttfamily,
%	moredelim=[l][\color{orange}]{\&},
%	moredelim=[l][\color{magenta}]{*},
%	moredelim=**[il][\YAMLcolonstyle{:}\YAMLvaluestyle]{:},   % switch to value style at :
%	morestring=[b]',
%	morestring=[b]",
%	literate =		{---}{{\ProcessThreeDashes}}3
%					{>}{{\textcolor{red}\textgreater}}1
%					{|}{{\textcolor{red}\textbar}}1
%					{\ -\ }{{\mdseries\ -\ }}3,
%}
%
%% switch to key style at EOL
%\lst@AddToHook{EveryLine}{\ifx\lst@language\language@yaml\YAMLkeystyle\fi}
%
%\newcommand\ProcessThreeDashes{\llap{\color{cyan}\mdseries-{-}-}}

% Umożliwienie korzystania z polskich liter w listingach kodu

\lstset{
	prebreak=\raisebox{0ex}[0ex][0ex]{\ensuremath{\hookleftarrow}},
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
\captionsetup[lstlisting]{font={small}}

% Nierozjechane linki w tytułowiej stronie informacyjnej

\RequirePackage{listliketab}

% Włączenie nagłówków na każdej stronie z informacją o numerze strony i tytułem

\RequirePackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[LE,RO]{\thepage}
\fancyhead[LO]{\sc\nouppercase{\rightmark}}
\fancyhead[RE]{\sc\leftmark}
%\renewcommand{\footrulewidth}{0.4pt}

\renewcommand{\chaptermark}[1]{\markboth{\thechapter.\enspace#1}{}}
%\renewcommand{\sectionmark}[1]{\markright{\thesection.\enspace#1}}
%\def\cleardoublepage{\clearpage\if@twoside
%	\ifodd\c@page\else\hbox{}\thispagestyle{empty}\newpage
%	\if@twocolumn\hbox{}\newpage\fi\fi\fi}
%\renewcommand{\@seccntformat}[1]{\csname the#1\endcsname.\enspace}
%\renewcommand{\numberline}[1]{\hb@xt@\@tempdima{#1.\hfil}}
\RequirePackage[parfill]{parskip}[2001/04/09]
\RequirePackage{setspace}
%\onehalfspacing
\linespread{1.15} % zalecenie Rektora
\frenchspacing
\clubpenalty=10000
\widowpenalty=10000
\brokenpenalty=10000

% Umożliwienie korzystania z przypisów

\RequirePackage{footnote}
%\RequirePackage[all]{hypcap}
%\RequirePackage{tikz}
%\usetikzlibrary{matrix}

% Font URLi i zawijanie bardzo długich adresów URL (ładować po paczce setspace,
% żeby działały dobrze skoki do footnote)

%\RequirePackage{url}
%\PassOptionsToPackage{hyphens}{url}
%\RequirePackage[unicode,plainpages=false,hypertexnames=true]{hyperref}
\RequirePackage[unicode]{hyperref}

% Zwykły \href z emph font

\newcommand\hrefemph[2]{%
	\href{#1}{\emph{#2}}%
}

% Zwykły \href z verbatim font

\newcommand\hreftt[2]{%
	\href{#1}{\texttt{#2}}%
}

% Zwykły \gls z verbatim font

\newcommand\glstt[2]{%
	\texttt{\glslink{#1}{#2}}%
}

% Zwykły \glslink z verbatim font

\newcommand\glslinktt[2]{%
	\glslink{#1}{\texttt{#2}}%
}

%\let\oldhref\href
%\renewcommand{\href}[2]{\oldhref{#1}{#2}}

% Ustawienia słownika pojęć (glossaries)

\RequirePackage[nomain,acronym,xindy={language=polish,codepage=utf8},nonumberlist]{glossaries}
%\RequirePackage{glossary-mcols} % for 2 columns \printglossary[style=mcolindex]
%\renewcommand*{\glstextformat}{\texttt} % font dla odwołań \gls
\renewcommand{\glsnamefont}[1]{\textbf{#1}} % font dla haseł w słowniku
\renewcommand*{\glspostdescription}{}
\newglossarystyle{labeling}{%
	\renewenvironment{theglossary}%
		{\begin{longtable}{p{.15\linewidth}p{1.55\glsdescwidth}}}%
		{\end{longtable}}%
	\renewcommand*{\glspostdescription}{\\}%
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
\renewcommand{\mkbegdispquote}[2]{\itshape} % chcemy pochylone cytowania
%\DeclareQuoteOption{polish} % Package csquotes Warning: '\DeclareQuoteOption' invalid at this point

% Ustawienia dot. bibliografii

\RequirePackage[
	style=numeric,
%	style=apa,
	backend=biber,
	sorting=nyt,
	backref=true
]{biblatex}
\DeclareLanguageMapping{polish}{english-apa}
\addbibresource{bibliography.bib}

% Paczki dla matematycznych formuł

\RequirePackage{mathtools} % do not use old amsmath package
%\RequirePackage{amsthm}
\RequirePackage{amssymb}
%\RequirePackage{mathabx}

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
\def\supervisoremail#1{\gdef\@supervisoremail{#1}}
\def\@supervisoremail{\@latex@error{No supervisor e-mail given}\@ehc}
\def\discipline#1{\gdef\@discipline{#1}}
\def\@discipline{\@latex@error{No discipline given}\@ehc}
\def\monthyear#1{\gdef\@monthyear{#1}}
\def\@monthyear{\@latex@error{No month and year given}\@ehc}
%\def\date#1{\gdef\@date{#1}}
%\def\@date{\@latex@error{No date given}\@ehc}
\def\album#1{\gdef\@album{#1}}
\def\@album{\@latex@error{No album number given}\@ehc}
\newcommand{\university}{Politechnika Warszawska}
\newcommand{\faculty}{Wydział Matematyki \protect\\i~Nauk Informacyjnych}
\newcommand{\location}{Warszawa}
\newcommand{\authorsig}{podpis autora}
\newcommand{\supervisorsig}{podpis promotora}
\newcommand{\titlepagecap}{Strona tytułowa}
%\def\@statementcap{Oświadczenie}
%\def\@definition{Definicja}
%\def\@corollary{Wniosek}
%\def\@remark{Uwaga}
%\def\@example{Przykład}

% Załączniki

\RequirePackage[toc,page]{appendix}

\def\zalaczniki{Załączniki}
\renewcommand{\appendixtocname}{\zalaczniki}
\renewcommand{\appendixpagename}{\zalaczniki}

% Wyświetlanie drzewa katalogów

\usepackage{dirtree}

% Graficzne schematy protokołów.

\RequirePackage{bytefield}
\RequirePackage{multirow}

\let\oldbitbox\bitbox
\renewcommand{\bitbox}[2]{%
	\oldbitbox{#1}{\texttt{#2}}%
}

\let\oldwordbox\wordbox
\renewcommand{\wordbox}[3][lrbt]{%
	\oldwordbox[#1]{#2}{\texttt{#3}}%
}

% Zmiana nazw tabeli (AtBeginDocument, aby zmusić paczkę babel)

\AtBeginDocument{%
	\renewcommand\tablename{Tabela}
}

% Nie rób nowej linii przed wypunktowaniami

\newcommand\mynobreakpar{\par\nobreak\@afterheading}

% Strona tytułowa

\newcommand\universitybox{\Huge\adagioregular\textbf{\university}}
\newcommand\facultybox{\fontsize{19}{13}\selectfont\adagioregularmorespace\addfontfeature{LetterSpace=45.0}\fakesc{\faculty}}

\renewcommand{\maketitle}{
	\pdfbookmark[0]{\titlepagecap}{titlepage}
	\begin{titlepage}
		\center
		% Logo MiNI
		\begin{minipage}{2.6cm}
			\includegraphics[width=2.6cm]{img/mini}
%			\hfill % odkomentuj i wywal powyższe jeśli tak Rektor chce
		\end{minipage}
		\hfill
		% Napis z nazwą Uczelni i Wydziału
		\begin{minipage}{110mm}
			\begin{center}
				\universitybox\\\vspace{3mm}\facultybox
			\end{center}
		\end{minipage}
		\hfill
		% Logo PW
		\begin{minipage}{2.6cm}
			\begin{flushright}
				\includegraphics[width=2.6cm]{img/pw}
			\end{flushright}
		\end{minipage}\par
		\vspace{3.5cm}

		% Praca magisterska

		{
			{\fontsize{45}{50}\selectfont\adagiolight Praca dyplomowa magisterska}\\[0.7cm]
			{\fontsize{12}{15}\selectfont na kierunku \@discipline}
		\par}

		\vspace{1.5cm}

		% Tytuł pracy

		\begin{minipage}{0.75\textwidth}
			\begin{spacing}{1.7}
				\center\textbf{\Large\@title}
			\end{spacing}
		\end{minipage}

		\vspace{0.7cm}

		% Autor

		{\Huge\adagioregular\@author}\\[0.2cm]
		{\fontsize{12}{15}\selectfont Numer albumu 237533}

		\vspace{0.7cm}

		% Promotor

		{\fontsize{12}{15}\selectfont promotor}\\[0.2cm]
		\@supervisor\\[2.5cm]

		\vfill

		% Miejscowość i rok

		\textsc{\large\MakeUppercase{\location}~\@monthyear}

		\vspace{5mm}

		% Podpisy autora i promotora na odwrocie

		\clearpage
		\thispagestyle{empty}
		\null\vfill
		\newcommand{\sigdots}{.............................................}

		% Miejsce na podpis promotora

		\begin{minipage}{50mm}
			\begin{center}
				\sigdots\\
				\vspace{1mm}
				\supervisorsig
			\end{center}
		\end{minipage}
		\hfill
		% Miejsce na podpis autora
		\begin{minipage}{50mm}
			\begin{center}
				\sigdots\\
				\vspace{1mm}
				\authorsig
			\end{center}
		\end{minipage}
	\end{titlepage}}
\endinput
