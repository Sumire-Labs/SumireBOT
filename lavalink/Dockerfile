# Lavalink Music Server Container
FROM eclipse-temurin:21-jre-alpine

WORKDIR /opt/lavalink

# Install wget for healthcheck
RUN apk add --no-cache wget

# Create plugins directory
RUN mkdir -p /opt/lavalink/plugins

EXPOSE 2333

# Run Lavalink (JAR and config mounted as volumes)
CMD ["java", "-jar", "Lavalink.jar"]
