#!/bin/bash
su ubuntu
source ~/anaconda3/etc/profile.d/conda.sh
conda activate slomo
aws s3 sync s3://slomo-checkpoints/ ./checkpoints/
cd /home/ubuntu/Super-SloMo
git pull
python3 script.py