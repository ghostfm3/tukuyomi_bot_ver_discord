FROM nvidia/cuda:11.4.3-cudnn8-runtime-ubuntu20.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git

WORKDIR /app

RUN pip install -r requirements.txt

COPY src /app/src

CMD ["python3", "discord_bot.py"]