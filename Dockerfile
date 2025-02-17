FROM python:3.8

# this will be the working directory inside of the image
WORKDIR /usr/src/app

# copy python library requirements.txt
COPY requirements.txt ./

# install python library requirements
RUN pip install -r requirements.txt

# execute the python application
CMD ["python", "run.py"]