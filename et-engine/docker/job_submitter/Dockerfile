FROM public.ecr.aws/amazonlinux/amazonlinux:2

RUN yum install -y python3 python3-pip

WORKDIR /app
ADD . /app

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "submit_jobs.py"]