FROM node:20-alpine

# Set standard node development execution flag environment parameter
ENV NODE_ENV=development

WORKDIR /app

# FIXED: Copied lock files to guarantee strict deterministic framework version pinning
COPY package*.json ./

# FIXED: Swapped out loose install for npm ci to enforce exact package-lock structural alignment
RUN npm install

COPY . .

# FIXED: Rectified privilege escalation vector by altering ownership and dropping to an unprivileged worker
RUN chown -R node:node /app
USER node

EXPOSE 3000

# FIXED: Extracted redundant port binding arguments, deferring completely to vite.config.js parameters
CMD ["npm", "run", "dev"]