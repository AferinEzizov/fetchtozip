FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirments.txt
CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
