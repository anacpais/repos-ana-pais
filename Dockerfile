FROM python:3.12-slim
WORKDIR /app
COPY app.py docs.html ./
COPY dados ./dados
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
USER 10001
EXPOSE 8000
CMD ["python", "app.py"]
