#!/usr/bin/env bash

ROOT=$(dirname "${BASH_SOURCE}")/..

cd ${ROOT}
rm -rf generated
mkdir -p generated/img
cp -r content/* generated/
exec python ./src/generate.py $@
cd - > /dev/null
