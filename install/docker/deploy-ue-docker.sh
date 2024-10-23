#!/bin/bash

INST_DIR=/opt
export GIT_BRANCH=master
cd ${INST_DIR}
if [ ! -d "${INST_DIR}/updatengine-server" ]; then
    git clone https://github.com/updatengine-ng/updatengine-server -b ${GIT_BRANCH}
fi
cp -r custom ${INST_DIR}/updatengine-server/install/docker/
${INST_DIR}/updatengine-server/install/docker/install.sh

