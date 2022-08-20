FROM python:3.9

LABEL coder1="Cheng"
LABEL coder2="Meihu"
LABEL description="DAMG 7245 Big Data Summer 2022 Assignment 3"
LABEL version="v2.0.0"



COPY . /app

WORKDIR /app/src

RUN pip install --upgrade pip
RUN pip install -r ../requirements.txt

#RUN python3 ./src/readInput.py 
CMD python3 main.py


EXPOSE 3000
EXPOSE 4000


