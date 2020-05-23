.PHONY:
black:
	@black -t py38 -S .

watch:
	@python -m r3build

generate_model:
	@python -m r3build.internal.defconv model ./r3build.def.toml | black -q - > ./r3build/config_model.py

generate_skeleton:
	@python -m r3build.internal.defconv skel ./r3build.def.toml | black -q - > ./r3build.skeleton.toml
