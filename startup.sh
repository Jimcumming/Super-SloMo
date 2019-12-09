#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate slomo
aws s3 cp s3://slomo-checkpoints/default.ckpt /home/ubuntu/checkpoints/default.ckpt
cd /home/ubuntu/Super-SloMo
git pull
python script.py