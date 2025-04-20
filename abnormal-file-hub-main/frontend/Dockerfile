# Stage 1: Build the React application
FROM node:18-alpine as build

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./
# If using yarn, copy yarn.lock instead and use yarn install
# COPY yarn.lock ./

# Install dependencies
RUN npm install
# If using yarn: RUN yarn install --frozen-lockfile

# Copy the rest of the application code
COPY . .

# Set the API URL build argument (can be overridden at build time)
ARG REACT_APP_API_URL=http://localhost:8000/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build the application for production
RUN npm run build

# Stage 2: Serve the built application using Nginx
FROM nginx:1.25-alpine

# Copy the built files from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom Nginx configuration if needed
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for Nginx
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"] 