FROM python:3.8-alpine3.11

RUN pip install \
    'python-telegram-bot>=12.4' \
&& mkdir -p /bot

COPY ./* /bot/

WORKDIR /bot

CMD ["/usr/local/bin/python", "/bot/bot.py"]