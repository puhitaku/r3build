.PHONY:
black:
	@black -t py38 -S .

watch:
	@python -m r3build

