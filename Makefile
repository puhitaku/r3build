.PHONY:
black:
	@black -t py38 -S .

clean:
	@rm -r $$(find . | grep pyc)

watch:
	@python -m r3build

generate_skeleton:
	@python -m r3build.internal.defconv skel ./r3build.def.toml | black -q - > ./r3build.skeleton.toml

generate_class_definition:
	@python -m r3build.internal.defconv cls ./r3build.def.toml | black -q - > ./r3build/config_class.py
