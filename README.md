# FastAPI Blog API

A blog API built with FastAPI, featuring Authentication, Redis caching, PostgreSQL database integration, and comprehensive testing.

## Features
- JWT Authentication
- Blog Post CRUD Operations
- PostgreSQL Database
- Redis Caching
- Docker Deployment
- Nginx Reverse Proxy
- Automated Tests

## Build and start the containers:
docker-compose up --build -d

## Access the API:
- API Documentation: http://localhost/docs
- API Endpoints: http://localhost/api

## API Endpoints
### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login and get JWT token

### Blog Posts
- `GET /api/posts` - List all posts
- `POST /api/posts` - Create new post
- `GET /api/posts/{id}` - Get specific post
- `PUT /api/posts/{id}` - Update post
- `DELETE /api/posts/{id}` - Delete post

## Running Tests
docker-compose exec web pytest
