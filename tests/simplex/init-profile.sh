#!/bin/bash
# Initialize profile with display name passed as argument
echo "/u $1" | simplex-chat -d /home/simplex/data
echo "/quit" | simplex-chat -d /home/simplex/data
