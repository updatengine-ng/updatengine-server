# UpdatEngine-server

Version 2.2.0

UpdatEngine Server is a web app allowing people to inventory computer an server, deploy software and create profile to apply on inventoried machines for Windows and Linux.

- [History](#history)
- [What's new](#whats-new-)
- [Install](#install)
- [Upgrade from 2.1.1/Django 1.6.2](#upgrade-from-211django-162)
- [Update](#update)
- [Links](#links)
- [License](#license)

## History
UpdatEngine client and server was originally written by Yves Guimard.
He had to stop his participation in the project in July 2017.
Since version 2.1.1 of 2014, there was not much evolution for the server part and this repository has no other pretensions than to try to improve the functionalities.
Thanks to Yves, to the developers who participated and still participates as well as to the users.

## What's new ?
UpdatEngine-server was upgraded :
- Django 1.11 LTS
- Deprecated migration tool 'South' removed
- Display column 'Operating system' added and 'Comment' removed from inventory machines
- New menu "General configuration" with theses options :
  - Remove duplicated machines
  - Hide 'Warning' messages in deployment history
- Script 'clear_history' to add in schedule task
- 100% compatibility with [**UpdatEngine-client 2.4.9.4**](https://github.com/dam09fr/updatengine-client/releases)
- Tested with Debian 8, Ubuntu 16.04, Ubuntu 18.04, CentOs 7

## Install
See [**2.1.1 installation documentation**](https://updatengine.com/) for details

Quickly (for debian/ubuntu):
  ```
sudo apt-get install apache2 libapache2-mod-wsgi python2.7 python-virtualenv python-pip libxml2-dev libxslt-dev python-dev libmysqlclient-dev git-core mysql-server
sudo virtualenv --distribute --no-site-packages -p /usr/bin/python2.7 /var/www/UE-environment
cd /var/www/UE-environment/
sudo git clone https://github.com/noelmartinon/updatengine-server

sudo /var/www/UE-environment/bin/pip install --upgrade distribute
sudo /var/www/UE-environment/bin/pip install --upgrade setuptools
sudo /var/www/UE-environment/bin/pip install -r /var/www/UE-environment/updatengine-server/requirements/pip-packages.txt

mysqladmin -u root -p create updatengine
mysql -u root -p -e "GRANT ALL PRIVILEGES ON updatengine.* TO 'updatengineuser'@'localhost' IDENTIFIED by 'unmotdepasse' WITH GRANT OPTION;"
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql
# You may see some warnings such as below, but don't worry about this. This files are used by 'tzselect' linux command and are not timezone.
# Warning: Unable to load '/usr/share/zoneinfo/iso3166.tab' as time zone. Skipping it.
# Warning: Unable to load '/usr/share/zoneinfo/leap-seconds.list' as time zone. Skipping it.
# Warning: Unable to load '/usr/share/zoneinfo/zone.tab' as time zone. Skipping it.
# Warning: Unable to load '/usr/share/zoneinfo/zone1970.tab' as time zone. Skipping it.
sudo service mysql restart

sudo cp /var/www/UE-environment/updatengine-server/updatengine/settings.py.model /var/www/UE-environment/updatengine-server/updatengine/settings.py
# and now modify settings.py

sudo cp /var/www/UE-environment/updatengine-server/requirements/apache-updatengine.conf /etc/apache2/sites-available/apache-updatengine.conf
sudo a2ensite apache-updatengine
sudo a2enmod wsgi
sudo service apache2 restart

sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py migrate

sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/configuration_initial_data.yaml
sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/groups_initial_data.yaml

sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/static/
sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/media/

sudo service apache2 restart

sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py createsuperuser
  ```

## Upgrade from 2.1.1/Django 1.6.2
Since UE Server now uses Django 1.11.13 and its integrate migration tools with new initial migration files, here is a clean solution to upgrade and keep your database.
After this upgrade, next 'migrations' will be easier than the procedure below.

Quickly (for debian/ubuntu):
  ```
# Backup existing database (for security reason)
# To restore : 'mysqladmin -u root -p drop updatengine' then
# recreate empty db and 'gunzip < ~/updatengine.sql.gz | mysql -u root -p updatengine'
mysqldump -u root -p updatengine | gzip -9 > ~/updatengine.sql.gz

# Move existing UE site (backup old version)
sudo mv /var/www/UE-environment/ /var/www/UE-environment_1.6.2/

# Install new version
sudo virtualenv --distribute --no-site-packages -p /usr/bin/python2.7 /var/www/UE-environment
cd /var/www/UE-environment/
sudo git clone https://github.com/noelmartinon/updatengine-server

sudo /var/www/UE-environment/bin/pip install --upgrade pip distribute setuptools
sudo /var/www/UE-environment/bin/pip install -r /var/www/UE-environment/updatengine-server/requirements/pip-packages.txt

sudo cp /var/www/UE-environment/updatengine-server/updatengine/settings.py.model /var/www/UE-environment/updatengine-server/updatengine/settings.py
# and now MODIFY settings.py

# Adapt the database ( add new fields, fake migration, remove 'south' table)
/var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py dbshell

ALTER TABLE inventory_entity ADD ip_range VARCHAR(200);
CREATE TABLE `configuration_globalconfig` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(100) NOT NULL, `show_warning` varchar(3) NOT NULL, `remove_duplicate` varchar(3) NOT NULL);
DROP TABLE IF EXISTS `south_migrationhistory`;
DROP TABLE IF EXISTS `django_migrations`;
quit

sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py migrate --fake-initial

# Here, your global deployment period is reset to initial value
# so keep in mind that you must set your own values in configuration menu
sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/configuration_initial_data.yaml
sudo /var/www/UE-environment/bin/python /var/www/UE-environment/updatengine-server/manage.py loaddata /var/www/UE-environment/updatengine-server/initial_data/groups_initial_data.yaml

# Copy deployment packages
rsync -av /var/www/UE-environment_1.6.2/updatengine-server/updatengine/media/package-file/* /var/www/UE-environment/updatengine-server/updatengine/media/package-file/

sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/static/
sudo chown -R www-data:www-data /var/www/UE-environment/updatengine-server/updatengine/media/

sudo service apache2 restart

# If new site works perfectly then delete old UE site (DANGER impossible to go back):
# sudo rm -rf /var/www/UE-environment_1.6.2
  ```

## Update
To update an existing version do :
  ```
cd /var/www/UE-environment/updatengine-server/
sudo git checkout --track origin/master
sudo git pull
sudo service apache2 restart
  ```
Currently, there is no change to the structure of the database so there is no need to update it with ```manage.py migrate```
  
## Links
- French Google discussion group : https://groups.google.com/forum/#!forum/updatengine-fr
- Old official site : https://updatengine.com/
- Site archive : https://web.archive.org/web/20170318143615/http://www.updatengine.com:80/
- Github Damien GUILLEM : https://github.com/dam09fr/

## License
GPL-2.0
