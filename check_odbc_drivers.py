#!/usr/bin/env python3
"""Check available ODBC drivers."""

import pyodbc

print("Available ODBC drivers:")
for driver in pyodbc.drivers():
    print(f"  - {driver}")
