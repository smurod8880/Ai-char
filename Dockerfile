FROM python:3.11-slim

# Установка зависимостей
RUN apt-get update && \
    apt-get install -y build-essential wget gcc

# Установка TA-Lib C библиотеки
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Симлинки, чтобы Python TA-Lib находил библиотеку
RUN ln -s /usr/local/lib/libta_lib.so /usr/lib/libta_lib.so
RUN ln -s /usr/local/include/ta-lib /usr/include/ta-lib

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
