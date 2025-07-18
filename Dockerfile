FROM python:3.11-slim

# Устанавливаем зависимости для сборки TA-Lib
RUN apt-get update && \
    apt-get install -y build-essential wget gcc

# Скачиваем и собираем TA-Lib C-библиотеку
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Проверяем, что библиотеки появились!
RUN ls /usr/lib | grep ta_lib && ls /usr/include/ta-lib

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
