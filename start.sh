#!/bin/bash

# Clean up Xvfb locks if any exist
echo "Cleaning up Xvfb locks..."
rm -f /tmp/.X99-lock

# Clean up Chromium SingletonLock in the persistent data volume
echo "Cleaning up Chromium persistent SingletonLock..."
rm -f data/browser/SingletonLock
rm -f data/browser/Default/SingletonLock

# Start Xvfb in the background with access control disabled (-ac)
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1280x720x24 -ac +extension RANDR &
export DISPLAY=:99

# Start x11vnc server to expose the display on port 7900 (for VNC visual control/manual login)
echo "Starting x11vnc..."
x11vnc -display :99 -forever -nopw -shared -rfbport 7900 -bg &

# Wait a second for Xvfb to start
sleep 2

# Start Uvicorn
echo "Starting Uvicorn..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8005
