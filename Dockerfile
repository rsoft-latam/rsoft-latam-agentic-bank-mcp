FROM public.ecr.aws/lambda/python:3.11
WORKDIR ${LAMBDA_TASK_ROOT}

ENV PIP_ONLY_BINARY=:all:
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt   # <-- sin --target

COPY app/ ./app
CMD ["app.main.lambda_handler"]