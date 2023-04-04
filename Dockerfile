FROM python:3.9
LABEL version='0.1' maintainer='marc.puig@gmail.com'

RUN apt-get update && apt-get install -y ca-certificates wget
#RUN pip3 install --upgrade pip

WORKDIR /app

COPY requirements.txt ./
ADD src ./src
ADD data ./data
RUN pip install -r requirements.txt

COPY .env ./

# Start the application
EXPOSE 8000
CMD ["/usr/local/bin/uvicorn", "--host", "0.0.0.0", "--port", "8000", "src.main:app", "--reload", "--workers", "1"]
