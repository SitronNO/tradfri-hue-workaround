FROM python:3-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./tradfri_hue_workaround.py /code/tradfri_hue_workaround.py
ENV CONFIGFILE=/code/config.ini 

CMD ["python", "tradfri_hue_workaround.py"]

