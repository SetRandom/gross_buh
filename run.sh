#!/bin/bash
echo 'Start server. Sleep 10 sec...'
sleep 10
python3 db_migrate.py
python3 gross_buh.py
