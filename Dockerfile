FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY pom.xml .
COPY .mvn .mvn
RUN mvn dependency:resolve -q

COPY src ./src
COPY native ./native
RUN mvn clean package -q -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/virtual-threads-demo-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
