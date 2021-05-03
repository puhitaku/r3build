.PHONY: black-check black \
        clean distclean \
		build \
		deploytest deploy \
		watch \
		generate_skeleton generate_class_definition

black-check:
	@black --check -t py38 -l 100 -S .

black:
	@black -t py38 -l 100 -S .

clean:
	@rm -r $$(find . | grep pyc)

distclean:
	@rm -rf dist

build:
	python setup.py sdist

deploytest:
	twine upload --repository testpypi dist/*

deploy:
	twine upload --repository pypi dist/*

watch:
	@r3build

generate_skeleton:
	@python -m r3build.internal.defconv skel ./r3build.def.toml | black -q - > ./r3build.skeleton.toml

generate_class_definition:
	@python -m r3build.internal.defconv cls ./r3build.def.toml | black -q - > ./r3build/config_class.py
