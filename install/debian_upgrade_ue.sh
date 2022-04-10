#!/bin/bash

################################################
## UpdatEngine-server upgrade script
## 2022/04/10
################################################
#
#             /!\ INFORMATION /!\
#
# Upgrade UE-server (files, django, db)
#
################################################


## Must be root user to install
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root user"
    exit
fi


################################################
###  -- UE server installation settings --   ###
################################################

## Values required
export INST_DIR=/srv
export VENV_DIR=/srv/venv/ue


################################################
###      -- Installation process --          ###
################################################

# Update files
cd ${INST_DIR}/updatengine-server
git pull

# Update Django
source ${VENV_DIR}/bin/activate
pip install --upgrade pip
pip install -r requirements/pip-packages.txt

# Update current settings
grep -L "django.db.models.BigAutoField" updatengine/settings.py
if [ $? -eq 0 ]; then
cat <<EOF >> updatengine/settings.py
# Set default default type for primary keys
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EOF
fi

# Apply migration
python manage.py migrate

# Restart apache
service apache2 restart
