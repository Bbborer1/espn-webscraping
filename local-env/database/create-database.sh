#!/usr/bin/env bash

function retry {
  local n=1
  local max=5
  local delay=10
  while true; do
    if "$@"; then break
    else
      if [[ ${n} -lt ${max} ]]; then
        ((n++))
        echo "Command failed. Attempt $n/$max:"
        sleep ${delay};
      else
        echo "The command has failed after $n attempts."
        exit -1
      fi
    fi
  done
}

retry /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P Ready2go -d master -i /usr/src/app/create-database.sql

