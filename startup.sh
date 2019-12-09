#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate slomo
aws s3 sync /checkpoints s3://slomo-checkpoints
cd /home/ubuntu/Super-SloMo
git pull
python script.py