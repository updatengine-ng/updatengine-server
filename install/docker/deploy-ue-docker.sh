#!/bin/bash

INST_DIR=/opt
export GIT_BRANCH=master
apt install git gettext-base
cd ${INST_DIR}
if [ ! -d "${INST_DIR}/updatengine-server" ]; then
    git clone https://github.com/updatengine-ng/updatengine-server -b ${GIT_BRANCH}
else
    cd "${INST_DIR}/updatengine-server"
    git pull
    cd -
fi
cp -r custom ${INST_DIR}/updatengine-server/install/docker/
${INST_DIR}/updatengine-server/install/docker/install.sh

