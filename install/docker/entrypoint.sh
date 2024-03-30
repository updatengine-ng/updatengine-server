#!/bin/sh

# Defaults SECRET_KEY to a random value
SECRET_KEY_FILE=./secret_key
if [ -z $SECRET_KEY ]; then
    if [ ! -f $SECRET_KEY_FILE ]; then
        echo "Generate a secret key"
        dd bs=48 count=1 if=/dev/urandom 2>/dev/null | base64 > $SECRET_KEY_FILE
        chmod go-r $SECRET_KEY_FILE
    fi
    export SECRET_KEY=`cat $SECRET_KEY_FILE`
else
    echo $SECRET_KEY > $SECRET_KEY_FILE
fi

# Create settings.py using environment settings
echo "Create settings.py"
envsubst < ./updatengine/settings.py.in > ./updatengine/settings.py
# Add 127.0.0.1 to avoid the error "Invalid HTTP_HOST header: '127.0.0.1:8000'. You may need 
# to add '127.0.0.1' to ALLOWED_HOSTS"
sed -i "s|^ALLOWED_HOSTS = \[|ALLOWED_HOSTS = \['127.0.0.1',|" ./updatengine/settings.py

# If settings_local.py exists, add it
if [ -f ./install/docker/custom.dist/settings_local.py ]; then
    cp ./install/docker/custom.dist/settings_local.py ./updatengine/settings_local.py
elif [ -f ./updatengine/settings_local.py ]; then
    rm ./updatengine/settings_local.py
fi

# Collect static files
echo "Collect static files"
python manage.py collectstatic --clear --noinput --verbosity=0

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate --noinput

# load initial data if needed
echo 'select count(*) from configuration_globalconfig;' | python manage.py dbshell | grep -v 'count' | grep 0 > /dev/null 2>&1
if [ "$?" = "0" ]; then
  echo "Import initial data"
  python manage.py loaddata initial_data/configuration_initial_data.yaml
  python manage.py loaddata initial_data/groups_initial_data.yaml
fi

# Start server
gunicorn updatengine.wsgi:application --bind 0.0.0.0:8000


