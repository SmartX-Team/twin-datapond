FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Install git
RUN apk add --no-cache git

# Clone the Unity Catalog UI repository
RUN git clone https://github.com/songinyong/unitycatalog-ui.git .

# Install dependencies using Yarn
RUN yarn install

# Expose the port the app runs on
EXPOSE 3000
EXPOSE 8081
# Run the app
CMD ["yarn", "start"]
