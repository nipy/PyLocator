all: html pdf

html: 
	sphinx-build -E -b html src build/html

pdf:
	sphinx-build -E -b latex src build/pdf/latex
	cd build/pdf/latex; make all-pdf; make clean
	cp build/pdf/latex/*.pdf build/pdf/

clean:
	rm -rf build


