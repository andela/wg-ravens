web: gunicorn wger.wsgi --log-file -
release: invoke create-settings --settings-path ./settings.py --database-path ./database.postgresql && invoke bootstrap-wger --settings-path ./settings.py --no-start-server && python manage.py makemigrations && python manage.py migrate