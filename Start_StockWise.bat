 
@echo off
title STOCKWISE INVENTORY SYSTEM

cd /d "C:\Users\Susmitha Gelasam\Downloads\StockWise_Industry_Homepage\Inventory_Management_System"

echo Starting StockWise...
echo.

if not exist main.py (
    echo ERROR: main.py not found!
    echo Check your project folder location.
    pause
    exit
)

py main.py

pause

