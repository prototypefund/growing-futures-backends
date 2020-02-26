FROM python:3.7.3-alpine3.9

WORKDIR /growf-admin/python
ADD . /growf-admin
RUN pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 5000

ENV MONGO_DB <db-name>
ENV DB_USER <db-user>
ENV DB_HOST <db-host>
ENV DB_PWD <db-pwd>
ENV PORT 5000

ENV BASE_URL <base-url>

CMD cd python
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 main:app
