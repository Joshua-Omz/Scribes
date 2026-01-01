# Use official Python image as base
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    postgresql-client \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --upgrade pip setuptools wheel

# Install pre-commit for git hooks
RUN pip install pre-commit

# Create a non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Set up the user (if not already created by base image)
RUN if ! id -u $USERNAME > /dev/null 2>&1; then \
    groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME; \
    fi

# Set default shell to bash
ENV SHELL=/bin/bash

# Install common Python packages for better dev experience
RUN pip install ipython ipdb
