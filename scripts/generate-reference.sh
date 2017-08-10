#!/usr/bin/env bash

ROOT=$(dirname "${BASH_SOURCE}")/..

cd ${ROOT}
rm -rf docs
mkdir -p docs/reference
cp -r content/* docs/
exec python3 ./src/generate.py $@
cd - > /dev/null
