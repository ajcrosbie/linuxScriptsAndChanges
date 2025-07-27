#!/bin/bash

# Add alias cls='clear' to ~/.bashrc only if it doesn't exist
if ! grep -q "alias cls=" ~/.bashrc; then
  echo "Adding 'cls' alias to ~/.bashrc"
  echo "alias cls='clear'" >> ~/.bashrc
else
  echo "'cls' alias already exists in ~/.bashrc"
fi

# Add 'git pall' alias only if not already set
if ! git config --global --get alias.pall > /dev/null; then
  echo "Setting up 'git pall' alias..."
  git config --global alias.pall '!f() {
    cur=$(git rev-parse --abbrev-ref HEAD);
    git fetch --all --prune;
    for b in $(git for-each-ref --format="%(refname:short)" refs/heads/); do
      git checkout "$b" >/dev/null 2>&1;
      if git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
        echo "Pulling $b...";
        git pull --ff-only;
      else
        echo "No upstream for $b, skipping.";
      fi;
    done;
    git checkout \"$cur\";
  }; f'
else
  echo "'git pall' alias already exists"
fi

# Add 'git undo' alias only if not already set
if ! git config --global --get alias.undo > /dev/null; then
  echo "Setting up 'git undo' alias..."
  git config --global alias.undo 'reset --soft HEAD~1'
else
  echo "'git undo' alias already exists"
fi
