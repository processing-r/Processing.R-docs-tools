#!/usr/bin/env bash

ROOT=$(dirname "${BASH_SOURCE}")/..

cd ${ROOT}
exec python ./src/generate.py $@
cd - > /dev/null
