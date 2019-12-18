#!/bin/bash
su ubuntu
source ~/anaconda3/etc/profile.d/conda.sh
conda activate slomo
aws s3 cp s3://slomo-checkpoints/default.ckpt /home/ubuntu/checkpoints/default.ckpt
cd /home/ubuntu/Super-SloMo
git pull
python3 script.py