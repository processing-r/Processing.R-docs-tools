#!/usr/bin/env bash

ROOT=$(dirname "${BASH_SOURCE}")/..

cd ${ROOT}
rm -rf docs
mkdir -p docs/img
cp -r content/* docs/
exec python ./src/generate.py $@
cd - > /dev/null
