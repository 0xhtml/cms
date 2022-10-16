run: env
	env/bin/flask --debug --app cms run

env: requirements.txt
	touch -c env
	test -d env || python -m venv env
	env/bin/pip install -r requirements.txt
