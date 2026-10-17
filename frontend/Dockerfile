# Image de développement du frontend RepoFlow.
FROM node:24-alpine

WORKDIR /app

# Dépendances d'abord pour le cache Docker.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# --host pour exposer le serveur Vite hors du conteneur.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
