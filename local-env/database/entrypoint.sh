#!/usr/bin/env bash

/opt/mssql/bin/sqlservr & /usr/src/app/create-database.sh & tail -f /dev/null