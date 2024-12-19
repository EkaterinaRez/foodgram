# build env
FROM node:22.9.0
WORKDIR /app
COPY package*.json ./
RUN npm install -g npm@11.0.0
COPY . ./
RUN npm run build
# CMD cp -r build result_build
CMD ["npx", "-y", "http-server", "-p", "7000", "/app/build"] 