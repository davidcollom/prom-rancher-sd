FROM python:3-alpine

COPY prom-rancher-sd.py /
RUN chmod +x /prom-rancher-sd.py
VOLUME /prom-rancher-sd-data
CMD ["/prom-rancher-sd.py"]
