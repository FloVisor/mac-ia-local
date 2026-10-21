FROM local/serena:2.1.0-5e4f5cd
RUN pip install --no-cache-dir uv
COPY reader.py repositories.json /reader/
ENTRYPOINT ["python", "/reader/reader.py"]
