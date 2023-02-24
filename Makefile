.PHONY : clean build upload

clean :
	python3 -m setup clean --all
	- rm -rf dist *.egg-info

build : clean
	tox
	python3 -m build

upload : build
	python3 -m twine check dist/*
	python3 -m twine upload dist/*
