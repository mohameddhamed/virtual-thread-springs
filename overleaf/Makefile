MAIN ?= main

.PHONY: all clean distclean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex config.tex template-guidance.tex elteikthesis.cls references.bib $(wildcard chapters/*.tex) $(wildcard figures/*.tex)
	latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error $(MAIN).tex

clean:
	latexmk -c $(MAIN).tex

distclean:
	latexmk -C $(MAIN).tex
