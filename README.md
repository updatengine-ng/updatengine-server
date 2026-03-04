# UpdatEngine-server

[![CI/CD Pipeline](https://github.com/Tronos83170/updatengine-server/actions/workflows/ci.yml/badge.svg)](https://github.com/Tronos83170/updatengine-server/actions/workflows/ci.yml)
[![License: GPL-2.0](https://img.shields.io/badge/License-GPL--2.0-blue.svg)](https://github.com/Tronos83170/updatengine-server/blob/master/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-5.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://github.com/Tronos83170/updatengine-server/blob/master/Dockerfile)

# UpdatEngine-server

UpdatEngine Server is a web app allowing people to inventory computer and server, deploy software and create profile to apply on inventoried machines for Windows and Linux.

* [History](#history)
* [Project features](#project-features)
* [Installation](#installation)
  * [Python Virtual Environment](#in-a-python-virtual-environment)
  * [Docker](#in-a-docker-container) 
* [Upgrade](#upgrade)
* [Examples](#examples-of-deployment-packages)
* [Links](#links)
* [License](#license)

## History

UpdatEngine client and server was originally written by Yves Guimard. He had to stop his participation in the project in July 2017. Since version 2.1.1 of 2014, there was not much evolution for the server part and this repository has no other pretensions than to try to improve the functionalities. Thanks to Yves, to the developers who participated and still participates as well as to the users.

## Project features

* Python 3.10+ / Django 4.2 LTS project
* Tested with Debian 10/11/12, Ubuntu 18.04/20.04/22.04/24.04

## Installation

UpdatEngine-server installation scripts for Debian/Ubuntu are located in the 'install' folder. 

### In a Python virtual environment

1. Preparation of configuration files

    If this preparation step is ignored, the step 2 installation will use default remote site settings 'debian/custom.dist/.env.default'.

    - Switch to the superuser account:

          sudo su -

    - Create a directory to store your settings and move into it (here in 'home' directory):

          mkdir ~/ue-config && cd $_

    - Create the 'custom' directory used by the installation script:

        It must be placed at the some level than 'install.sh' from step 2

          mkdir custom

    - Get default '.env' file and customize it:

      Customize your settings in this file (Installation directories, URL, database, SMTP...).

          wget -O ./custom/.env https://raw.githubusercontent.com/updatengine-ng/updatengine-server/master/install/debian/custom.dist/.env.default
          nano ./custom/.env

    - Optionally, get example 'settings_local.py' to customize some features:

      Customize additional settings in this file (LDAP, LOGGING...).

          wget -O ./custom/settings_local.py https://raw.githubusercontent.com/updatengine-ng/updatengine-server/master/install/debian/custom.dist/settings_local.py.example
          nano ./custom/settings_local.py

2. Installation

    - Get last installation script and run it:

          cd ~/ue-config
          wget -O install.sh https://raw.githubusercontent.com/updatengine-ng/updatengine-server/master/install/debian/install.sh
          chmod +x install.sh
          ./install.sh


    The script automaticaly update the python settings, the apache.conf and create auto-signed SSL certfificat.

### In a docker container

The distribution base image doesn't exist yet, so the container is built from source.

1. Preparation of configuration files

   If this preparation step is ignored, the step 2 installation will use default remote site settings 'docker/custom.dist/.env.default'.

   - Switch to the superuser account or to a user that is able to build and run docker:

          sudo su -

   - Create a directory to store your settings and move into it (here in 'home' directory):

          mkdir ~/ue-config && cd $_

    - Create the 'custom' directory used by the installation script:

        It must be placed at the some level than 'install-ue-docker.sh' from step 2

          mkdir custom

    - Get default '.env' file and customize it:

      Customize your settings in this file (Installation directories, URL, database, SMTP...).

          wget -O ./custom/.env https://raw.githubusercontent.com/updatengine-ng/updatengine-server/master/install/docker/custom.dist/.env.default
          nano ./custom/.env

    - Optionally, get example 'settings_local.py' to customize some features:

      Add additional settings in this file (LDAP, LOGGING...). All settings available for Django could be put in this file and the contains it is loading at the end of the 'settings.py', all values could be overridden 

          wget -O ./custom/settings_local.py https://raw.githubusercontent.com/updatengine-ng/updatengine-server/master/install/docker/custom.dist/settings_local.py.example
          nano ./custom/settings_local.py

2. Installation

    - Get last docker deployment script, customize INST_DIR and run it:

          cd ~/ue-config
          wget https://raw.githubusercontent.com/updatengine-ng/updatengine-server/master/install/docker/deploy-ue-docker.sh
          nano deploy-ue-docker.sh
          chmod +x deploy-ue-docker.sh
          ./deploy-ue-docker.sh

## Upgrade

> [!WARNING]
Before any upgrade, it's always recommended to backup the updatengine-server database, the current updatengine-server directory and possibly the Python venv directory.

### Before version 6.0.0:

Proceed with the same steps as those of the installation above using your own values ​​entered in your previous 'debian_install_ue.sh' script or your current 'updatengine/settings.py' file. Then run step 2 of the installation which will upgrade your database and project files.

### From version 6.0.0:

Go to your directory containing 'install.sh' and 'custom' directory and just run step 2 of the installation.

## Examples of deployment packages

### Mozilla Firefox 64bits

#### Package

* Name: Mozilla Firefox - 1_Install - 64bits\
  Description: Silent installation of Mozilla Firefox 64bits\
  Command: Firefox_Setup_70.0.1_64bits.exe -ms\
  Package file: Firefox_Setup_70.0.1_64bits.exe

#### Conditions

* Name: Mozilla Firefox < 70.0.1\
  Condition: Software not installed or version lower than\
  Software name: Mozilla Firefox \*\
  Version: 70.0.1

* Name: Windows 64bits\
  Condition: Windows 64 bits computer

### Java runtime environment 64bits

#### Package

* Name: Java Runtime Environment 8u231 64bits\
  Description: Silent installation of Java Runtime 64bits\
  Command:\
  wmic product where "name like ''Java%''" call uninstall /nointeractive\
  (rd "C:\\Program Files\\Java" /q /s || @echo on)\
  jre-8u231-windows-x64.exe /s\
  reg DELETE "HKLM\\SOFTWARE\\Wow6432Node\\JavaSoft\\Java Update" /f\
  download_no_restart\
  Package file: jre-8u231-windows-x64.exe

#### Conditions

* Name: JRE 8 Update 64 bits < 8.0.2310.11\
  Condition: Software not installed or version lower than\
  Software name: Java \* Update \* (64-bit)\
  Version: 8.0.2310.11

* Name: Windows 64bits\
  Condition: Windows 64 bits computer

### LibreOffice 64bits (Installation executed in user session and may be postpone)

#### Features

This package is a silent installation if there is no previous version or if there is no open user session.\
Else it prompts the user with a Window asking to install or cancel. After the countdown delay the installation start.\
If cancelling then UpdatEngine-client will check and ask again on next inventory.

#### Overall: Create package file

1. Create a working folder ***LibreOffice_6.2.8_Win_x64***

2. In that folder put the files [LibreOffice_6.2.8_Win_x64.msi](https://fr.libreoffice.org/donate/dl/win-x86_64/6.2.8/fr/LibreOffice_6.2.8_Win_x64.msi), [ExecAs.exe](https://github.com/noelmartinon/ExecAs/releases/download/1.1.0/ExecAs.exe), [setup_auto.exe](https://github.com/noelmartinon/setup_auto/releases/download/2.0/setup_auto.exe)

3. Create ***setup_auto.ini*** file:
   ```
   [SETUP]
   ; Time before auto execution in seconds
   TIMER_INSTALL_START=120

   ; Time showing the ending installation window in seconds
   TIMER_INSTALL_END=10

   ; Branding text
   BRANDING_TEXT=MY COMPANY NAME

   INFO_INSTALL_START=La procédure d'installation du logiciel va être executée automatiquement.\n\nCette procédure nécessite que les logiciels ci-dessous soient arrêtés et procédera à leur arrêt si vous ne l'avez pas fait :\n- %name%\n- Mozilla Firefox\n\nVous pouvez différer cette installation en cliquant sur le bouton [Annuler].\n\nDurée estimée de l'installation : 10 à 15 minutes

   INFO_INSTALL_END_OK=L'installation de %name% %version% a été effectuée avec succès.

   INFO_INSTALL_END_ERROR=L'installation de %name% %version% n'a pas pu être effectuée.

   ; Install is ignored if a the specified process is running
   ;QUIT_PROCESS_RUNNING=msiexec.exe

   ; Run in full silent mode when there is no previous installation (nothing to uninstall or no other version)
   ; Hide all auto_setup dialog boxes
   Auto_silent=1


   [PREINSTALL]
   ALWAYSOK_Fermeture des applications LibreOffice=taskkill /im soffice.bin /f
   ALWAYSOK_Fermeture de Mozilla Firefox=taskkill /im firefox.exe /f

   ; On preinstall error abort installation (except if marked 'ALWAYSOK_'):
   Abort_installation_on_error=1


   [UNINSTALL]
   Name=^LibreOffice.*
   ;Version=
   Arguments=/qn /norestart
   ; msisexec.exe uninstall arguments not required because it's the only one option:
   ;Arguments_msiexec=/qn /norestart

   ; On unsinstall error continue installation ? (1=abort)
   Abort_installation_on_error=1


   [INSTALL]
   Name=LibreOffice
   Version=6.2.8.2
   Command=msiexec /i LibreOffice_6.2.8_Win_x64.msi /qb! /norestart ALLUSERS=1 SELECT_WORD=1 SELECT_EXCEL=1 SELECT_POWERPOINT=1 USERNAME="" COMPANYNAME="MY COMPANY NAME" REGISTER_ALL_MSO_TYPES=1 UI_LANGS=fr ADDLOCAL=ALL RebootYesNo=No ISCHECKFORPRODUCTUPDATES=0 CREATEDESKTOPLINK=0 REMOVE=gm_o_Onlineupdate

   ; If application is already installed then abort
   ; Regular expression below and its optional exact 'Version' value are searched in installed programs list
   Abort_installed_name=^LibreOffice.*
   Abort_installed_version=6.2.8.2
   ```

4. Generate the encrypted installation command to hide admin login/password from users in the package:

   In a Windows shell go to your working directory and execute:
   ```
   ExecAs.exe -c -r -uADMINUSER -pPASSWORD -dNTDOMAIN -w setup_auto.exe
   ```

   Or you can also create a batch e.g. *admin_cmd_encrypt.bat* and double-click it:
   ```
   :: Generate the encrypted command
   @echo off
   ExecAs.exe -c -r -uADMINUSER -pPASSWORD -dNTDOMAIN -w setup_auto.exe
   echo.
   pause
   ```

   Then simply do [CTRL+V] in a window text (notepad) to paste and keep the result. Indeed, 'ExecAs -c' copies encrypted command to the clipboard ;)

5. Create ***install.bat*** and paste the above encrypted string:
   ```
   icacls "%temp%\updatengine" /grant *S-1-1-0:(OI)(CI)(RX)
   ExecAs.exe -i -w -h ExecAs.exe PASTE_HERE_THE_ENCRYPTED_COMMAND
   ```
   The user must be able to access to the temporary directory to execute msi file that's why 'icacls' is used.

6. Remove ***admin_cmd_encrypt.bat*** if it exists for not providing the administrator password in the package!

7. Compress your working directory in the package file *LibreOffice_6.2.8_Win_x64.zip*.\
   Be sure that all files are in root dirctory of this zip file else the commands would be for example 'LibreOffice_6.2.8_Win_x64\install.bat' and 'msiexec /i LibreOffice_6.2.8_Win_x64\LibreOffice_6.2.8_Win_x64.msi'

#### Package

* Name: LibreOffice 6.2.8 64bits\
  Description: Silent installation of LibreOffice 64bits\
  Command:\
  install.bat\
  download_no_restart\
  no_break_on_error\
  Package file: LibreOffice_6.2.8_Win_x64.zip

#### Conditions

* Name: LibreOffice < 6.2.8.2\
  Condition: Software not installed or version lower than\
  Software name: LibreOffice \*\
  Version: 6.2.8.2

* Name: Windows 64bits\
  Condition: Windows 64 bits computer

## Links
* Official site : https://updatengine-ng.com/
* French Google discussion group : https://groups.google.com/forum/#!forum/updatengine-fr

## License

GPL-2.0

