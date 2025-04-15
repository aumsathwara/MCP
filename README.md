# MCP Monorepo

This repository contains multiple MCP servers in separate subdirectories:

- **FileSystem-MCP**  
- **Weather-MCP**

Each sub-project has its own `pyproject.toml` so you can install them **individually** (e.g., if you only need one) or **all together** in the same environment.

## Repository Structure

```
MCP/
├── FileSystem-MCP/
│   ├── pyproject.toml
│   └── src/
│       └── custom_mcp/
│           ├── server.py
│           └── client.py
├── Weather-MCP/
│   ├── pyproject.toml
│   └── src/
│       └── weather_mcp/
│           └── server.py
└── (other files, readme, etc.)
```

## Installation Options

### 1. Install All MCPs Together (Single Command)

If you want **all** sub-projects in one environment, simply install the **top-level** project:

1) Case 1: If you have already setup uv project then: 
```bash
uv add "git+https://github.com/aumsathwara/MCP.git@multiple-mcps"
```
2) Case 2: If you haven't setup uv project then:
```bash
uv pip install "git+https://github.com/aumsathwara/MCP.git@multiple-mcps"
```
This pulls in the main monorepo at branch `multiple-mcps` and installs the top-level project as configured in `pyproject.toml`. Depending on your configuration, this may install all dependencies shared across the repository (though it might not pull in the subdirectory packages if they’re not referenced in the top-level pyproject). If you have references to each MCP at the top level, it should install them all.

> **Note**: If you see “Workspace dependency… must refer to local directory” or a similar error, you might need to install each sub-package separately (see below). Some versions of uv do not allow a single aggregator approach.

### 2. Install Just One Sub-Project (e.g., FileSystem-MCP)

Use **uv’s pip passthrough** and specify the subdirectory:

```bash
uv pip install "git+https://github.com/aumsathwara/MCP.git@multiple-mcps#subdirectory=FileSystem-MCP"
```

This tells pip to:

1. Clone the repo at branch `multiple-mcps`.
2. Navigate into `FileSystem-MCP/`.
3. Build and install that sub-package.

Now your environment has **FileSystem-MCP** installed.

### 3. Install Both Sub-Projects Manually

If you’d like both FileSystem-MCP and Weather-MCP in the **same** environment but **without** using the top-level aggregator, install each sub-package one by one:

```bash
uv pip install "git+https://github.com/aumsathwara/MCP.git@multiple-mcps#subdirectory=FileSystem-MCP"
uv pip install "git+https://github.com/aumsathwara/MCP.git@multiple-mcps#subdirectory=Weather-MCP"
```

That’s it! Now you have both installed. You can confirm by listing installed packages in your environment.

## Troubleshooting

1. **Workspace dependency errors**  
   If you see an error like:
   ```
   error: Workspace dependency 'mcp-all' must refer to local directory, not a Git repository
   ```
   it means uv does not allow referencing multiple subdirectories via a single aggregator `pyproject.toml` from Git. In that case, just use the “Install Both Sub-Projects Manually” approach above.

2. **Invalid subdirectory**  
   Make sure your path matches exactly (case-sensitive). If you see “file not found,” confirm your monorepo layout.

3. **Cannot find modules with dashes in the name**  
   Remember that Python import paths cannot contain a dash (`-`). Use underscores in package folder names (e.g., `weather_mcp`), but your distribution/package name in `pyproject.toml` can still have a dash (e.g., `name = "weather-mcp"`).

## Usage

After installation, each MCP project may expose its own console scripts (e.g., `filesystem-mcp-server`, `weather-mcp-server`), depending on how you configured `[project.scripts]` in each `pyproject.toml`. For example:

```bash
filesystem-mcp-server
```

…might start up the FileSystem-MCP server. Similarly,

```bash
weather-mcp-server
```

…starts the Weather-MCP server.

If not, you can always run them via Python modules. For example:

```bash
python -m custom_mcp.server
```

(or however you’ve structured your code).

## Contributing

1. Clone the repo:
   ```bash
   git clone -b multiple-mcps https://github.com/aumsathwara/MCP.git
   ```
2. Make changes in a feature branch.
3. Submit a pull request.
