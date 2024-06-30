FROM public.ecr.aws/amazonlinux/amazonlinux:2

RUN yum install -y python3 python3-pip
RUN python3 -m pip install boto3

WORKDIR /app
COPY . /app

CMD ["python3", "data_upload_task.py"]