FROM python:3.10

WORKDIR /app

COPY . .Z

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

RUN pip install torch==2.2.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

RUN pip install torchvision==0.17.2 -f https://download.pytorch.org/whl/cpu/torch_stable.html

RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.doubanio.com/simple

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

