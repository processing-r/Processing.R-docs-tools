#!/usr/bin/env bash

ROOT=$(dirname "${BASH_SOURCE}")/..

cd ${ROOT}
mv docs/.git cache.git.dir
rm -rf docs/
mkdir -p docs/reference
mv cache.git.dir docs/.git
cp -r content/* docs/
exec python3 ./src/generate.py $@
cd - > /dev/null
