#!/bin/bash

################################################
## UpdatEngine-server installation script with docker
## 2026/01/03
################################################

INST_DIR=/opt
export GIT_BRANCH=$(git -c 'versionsort.suffix=-' ls-remote --tags --sort='v:refname' https://github.com/updatengine-ng/updatengine-server.git | tail --lines=1 | cut --delimiter='/' --fields=3)
apt install git gettext-base
cd ${INST_DIR}
if [ ! -d "${INST_DIR}/updatengine-server" ]; then
    git clone https://github.com/updatengine-ng/updatengine-server -b ${GIT_BRANCH}
else
    cd "${INST_DIR}/updatengine-server"
    git fetch --all
    git reset --hard
    git checkout ${GIT_BRANCH}
    git reset --hard origin/${GIT_BRANCH}
    git pull
    cd -
fi
cp -r custom ${INST_DIR}/updatengine-server/install/docker/
${INST_DIR}/updatengine-server/install/docker/install.sh

