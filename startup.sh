#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate slomo
cd /home/ubuntu/Super-SloMo
git pull
python script.py