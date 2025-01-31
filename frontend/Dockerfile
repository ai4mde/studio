FROM node:18
WORKDIR /usr/src/app

COPY . /usr/src/app
RUN npm install --frozen-lockfile
RUN npm run build
ENTRYPOINT ["npm", "run", "dev", "--", "--host"]
