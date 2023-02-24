.PHONY : clean build upload

all: clean build upload

clean :
	python3 -m setup clean --all
	rm -rf dist *.egg-info

build :
	python3 -m build
	python3 -m twine check dist/*

upload :
	python3 -m twine upload dist/*
