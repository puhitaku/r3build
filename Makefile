.PHONY:
black:
	@black -t py38 -S .

watch:
	@python -m r3build

.ONESHELL:
generate_model:
	@python -m r3build.internal.defconv ./r3build.def.toml | black -q - > ./r3build/config_model.py
