#!/bin/bash

APP="$1"
OUT_DIR="out"

mkdir -p ${OUT_DIR}
tar -cvzf ${OUT_DIR}/${APP}.spl ${APP}