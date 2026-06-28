#!/bin/bash

cd ~/agentjw/projects/godmeme_bot

cp strategy.py strategy.py.bak.$(date +%s)
cp .env .env.bak.$(date +%s)

echo "Backup complete"
