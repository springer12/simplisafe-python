coverage:
	pipenv run py.test -s --verbose --cov-report term-missing --cov-report xml --cov=simplipy tests
init:
	pip install --upgrade pip pipenv
	pipenv lock
	pipenv install --dev
lint:
	pipenv run flake8 simplipy
	pipenv run pydocstyle simplipy
	pipenv run pylint simplipy
publish:
	python setup.py sdist bdist_wheel
	pipenv run twine upload dist/*
	rm -rf dist/ build/ .egg simplisafe_python.egg-info/
test:
	pipenv run py.test
