# Start from a minimal official image that already has Python 3.13.
# "slim" = fewer preinstalled packages → smaller image, smaller attack surface.
FROM python:3.13-slim

# The working directory inside the container. Subsequent paths are relative to it.
WORKDIR /app

# Copy ONLY requirements first, then install. Docker builds in cached layers:
# because this layer depends only on requirements.txt, editing main.py later does
# NOT invalidate it, so dependencies aren't reinstalled on every code change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code (main.py). .dockerignore keeps .venv etc. out.
COPY . .

# The API key is deliberately NOT baked into the image — a secret never belongs in
# an artifact that gets pushed to a registry. It's passed at runtime as an env var.
#
# --host 0.0.0.0 is REQUIRED inside a container: 127.0.0.1 would only be reachable
# from within the container itself; 0.0.0.0 accepts connections from outside it.
# Hosts like Cloud Run inject the port to listen on via $PORT (default to 8080).
#
# JSON/exec form ["sh","-c", ...] silences the JSONArgsRecommended warning AND
# lets ${PORT} expand. The `exec` makes uvicorn REPLACE the shell, so uvicorn
# becomes PID 1 and receives SIGTERM/SIGINT directly — clean shutdown on Ctrl+C
# locally and graceful shutdown when Cloud Run stops the container.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
