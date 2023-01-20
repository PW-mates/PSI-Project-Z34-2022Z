#!/bin/bash

docker build . -t ftp_server
docker stop ftp_server && docker rm ftp_server
docker run -d -p 21:21 -p 65000-65534:65000-65534 -p 990:990 --name ftp_server ftp_server
