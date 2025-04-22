FROM mongo:6.0

COPY init-mongo.sh /docker-entrypoint-initdb.d/

# Default MongoDB port
EXPOSE 27017

CMD ["mongod"] 