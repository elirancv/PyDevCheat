import httpx
from typing import Optional, Dict, List, Tuple
import re
import json
import logging
from pathlib import Path
import os
import yaml
from bs4 import BeautifulSoup
from ..utils import create_retry_decorator, handle_source_error, NetworkError, SourceError

logger = logging.getLogger(__name__)

class DevhintsSource:
    """A source that fetches cheat sheets from the rstacruz/cheatsheets GitHub repository."""
    
    # Create retry decorator for network requests
    retry_request = create_retry_decorator(
        max_attempts=3,
        min_wait=1,
        max_wait=10
    )
    
    def __init__(self):
        """Initialize the DevhintsSource."""
        self.base_url = "https://raw.githubusercontent.com/rstacruz/cheatsheets/master"
        self.api_url = "https://api.github.com/repos/rstacruz/cheatsheets/git/trees/master?recursive=1"
        self.topics_cache = {}
        self.local_cache_dir = Path(os.path.expanduser("~/.cache/pydevcheat/devhints"))
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = Path.home() / '.pydevcheat' / 'cache' / 'devhints'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'sheets.json'
        self.sheets_cache = self.cache_dir / 'sheets'
        self.sheets_cache.mkdir(exist_ok=True)

        # Common cheat sheets to pre-cache
        self.common_sheets = [
            'python.md',
            'javascript.md',
            'git.md',
            'bash.md',
            'docker.md',
            'react.md',
            'vim.md',
            'css.md',
            'html.md',
            'nodejs.md'
        ]
        
    @retry_request
    def _make_request(self, url: str, headers: Optional[Dict] = None) -> str:
        """Make a retryable HTTP request."""
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/plain"
            }
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout=10.0)
        response.raise_for_status()
        return response.text
        
    def search(self, query: str) -> Optional[str]:
        """
        Search for a cheatsheet by query and return its contents.
        Returns None if no results found or error occurs.
        """
        try:
            # Clean up query
            query = query.lower().replace(' ', '-')
            if not query.endswith('.md'):
                query += '.md'
                
            # Try local cache first
            local_file = self.local_cache_dir / query
            if local_file.exists():
                content = local_file.read_text(encoding='utf-8')
                return self._format_content(content)
                
            # Fetch from GitHub if not in cache
            content = self._make_request(f"{self.base_url}/{query}")
            
            # Cache the content locally
            local_file.write_text(content, encoding='utf-8')
            
            return self._format_content(content)
            
        except Exception as e:
            handle_source_error("devhints", e)
            return None
            
    def _format_content(self, content: str) -> str:
        """Format the markdown content with proper styling."""
        try:
            # Split frontmatter and content
            frontmatter, markdown = self._split_frontmatter(content)
            
            formatted_parts = []
            
            # Add title and intro if available
            if frontmatter:
                if 'title' in frontmatter:
                    formatted_parts.append(f"# {frontmatter['title']}\n")
                if 'intro' in frontmatter:
                    formatted_parts.append(f"{frontmatter['intro']}\n")
            
            # Add the main content
            formatted_parts.append(markdown.strip())
            
            return "\n".join(formatted_parts)
            
        except Exception as e:
            logger.error(f"Error formatting content: {e}")
            return content
            
    def _split_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter from markdown content."""
        frontmatter = {}
        markdown = content
        
        # Look for table-style frontmatter
        table_match = re.match(r'\|(.*?)\|(.*?)\|\n\|(.*?)\|(.*?)\|\n(.*)', content, re.DOTALL)
        if table_match:
            try:
                headers = [h.strip() for h in table_match.group(1).split('|')]
                values = [v.strip() for v in table_match.group(2).split('|')]
                frontmatter = dict(zip(headers, values))
                markdown = table_match.group(5)
            except:
                pass
        
        # Look for YAML-style frontmatter
        yaml_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
        if yaml_match:
            try:
                frontmatter = yaml.safe_load(yaml_match.group(1))
                markdown = yaml_match.group(2)
            except:
                pass
                
        return frontmatter, markdown
            
    def list_all_topics(self) -> Dict[str, str]:
        """List all available topics from the GitHub repository."""
        try:
            if self.topics_cache:
                return self.topics_cache
                
            # Use the GitHub API to list files in the repository
            api_url = "https://api.github.com/repos/rstacruz/cheatsheets/git/trees/master?recursive=1"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/vnd.github.v3+json"
            }
            
            logger.debug(f"Fetching repository tree from GitHub API: {api_url}")
            response = httpx.get(api_url, headers=headers, timeout=10.0)
            
            if response.status_code != 200:
                logger.error(f"GitHub API returned status code {response.status_code}: {response.text}")
                return self._get_fallback_topics()
                
            data = response.json()
            logger.debug(f"Got response from GitHub API with {len(data.get('tree', []))} items")
            
            topics = {}
            md_files = [item for item in data.get('tree', []) if item.get('path', '').endswith('.md')]
            logger.debug(f"Found {len(md_files)} markdown files")
            
            for item in md_files:
                path = item.get('path', '')
                if path != 'README.md':
                    # Remove .md extension and convert to title
                    title = path[:-3].replace('-', ' ').title()
                    logger.debug(f"Processing file: {path} -> {title}")
                    
                    # Determine category based on filename prefix
                    category = self._determine_category(path)
                    topics[title] = category
                    logger.debug(f"Added topic {title} to category {category}")
            
            if not topics:
                logger.warning("No topics found in GitHub response, using fallback")
                return self._get_fallback_topics()
                
            logger.info(f"Successfully loaded {len(topics)} topics from GitHub")
            self.topics_cache = topics
            return topics
            
        except Exception as e:
            logger.error(f"Error fetching topics from GitHub: {e}")
            return self._get_fallback_topics()
            
    def _get_title_from_file(self, path: str) -> Optional[str]:
        """Try to extract the title from a file's frontmatter."""
        try:
            url = f"{self.base_url}/{path}"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/plain"
            }
            
            response = httpx.get(url, headers=headers, follow_redirects=True, timeout=10.0)
            
            if response.status_code != 200:
                return None
                
            frontmatter, _ = self._split_frontmatter(response.text)
            return frontmatter.get('title')
            
        except Exception:
            return None
            
    def _determine_category(self, path: str) -> str:
        """Determine the category of a cheatsheet based on its filename."""
        category = "Others"
        
        # Common prefixes and their categories
        prefixes = {
            'js-': "JavaScript",
            'css-': "CSS",
            'html-': "HTML",
            'ruby-': "Ruby",
            'python-': "Python",
            'git-': "Git",
            'docker-': "DevOps",
            'rails-': "Rails",
            'vim-': "Vim",
            'react-': "React",
            'vue-': "Vue",
            'angular-': "Angular",
            'node-': "Node.js",
            'aws-': "AWS",
            'linux-': "Linux",
            'bash-': "CLI",
            'postgres-': "Databases",
            'mysql-': "Databases",
            'mongo-': "Databases"
        }
        
        # Check for prefix matches
        for prefix, cat in prefixes.items():
            if path.startswith(prefix):
                return cat
                
        # If no prefix match, try to determine category from path components
        if '/' in path:
            first_part = path.split('/')[0].lower()
            if first_part in ['javascript', 'js']:
                return "JavaScript"
            elif first_part in ['css', 'sass', 'less']:
                return "CSS"
            elif first_part in ['html', 'markup']:
                return "HTML"
            elif first_part in ['python', 'py']:
                return "Python"
            elif first_part in ['ruby', 'rb']:
                return "Ruby"
            elif first_part in ['git']:
                return "Git"
            elif first_part in ['docker', 'kubernetes', 'k8s']:
                return "DevOps"
            elif first_part in ['vim']:
                return "Vim"
            elif first_part in ['cli', 'terminal', 'shell']:
                return "CLI"
            elif first_part in ['db', 'sql', 'database']:
                return "Databases"
        
        return category
            
    def _get_fallback_topics(self) -> Dict[str, str]:
        """Return a predefined list of common topics."""
        return {
            # Analytics
            "analytics.js": "Analytics",
            "analytics": "Analytics",
            "mixpanel": "Analytics",
            "google_analytics": "Analytics",

            # Ansible
            "ansible": "Ansible",
            "ansible-examples": "Ansible",
            "ansible-guide": "Ansible",
            "ansible-modules": "Ansible",
            "ansible-roles": "Ansible",

            # Apps
            "atom": "Apps",
            "editorconfig": "Apps",
            "flashlight": "Apps",
            "inkscape": "Apps",
            "org-mode": "Apps",
            "sketch": "Apps",
            "spacemacs": "Apps",
            "sublime-text": "Apps",
            "vscode": "Apps",
            "weechat": "Apps",

            # C-like
            "c_preprocessor": "C-like",
            "csharp7": "C-like",
            "go": "C-like",

            # CLI
            "adb": "CLI",
            "animated_gif": "CLI",
            "ansi": "CLI",
            "bash": "CLI",
            "clip": "CLI",
            "composer": "CLI",
            "cron": "CLI",
            "curl": "CLI",
            "emacs": "CLI",
            "ffmpeg": "CLI",
            "find": "CLI",
            "fish-shell": "CLI",
            "gnupg": "CLI",
            "grep": "CLI",
            "homebrew": "CLI",
            "httpie": "CLI",
            "makefile": "CLI",
            "man": "CLI",
            "ncftp": "CLI",
            "pass": "CLI",
            "pm2": "CLI",
            "rename": "CLI",
            "rsync": "CLI",
            "rtorrent": "CLI",
            "scp": "CLI",
            "screen": "CLI",
            "sed": "CLI",
            "sh-pipes": "CLI",
            "sh": "CLI",
            "tar": "CLI",
            "tmux": "CLI",
            "top": "CLI",
            "watchexec": "CLI",
            "yum": "CLI",
            "zsh": "CLI",

            # CSS
            "bootstrap": "CSS",
            "bulma": "CSS",
            "css-antialias": "CSS",
            "css-flexbox": "CSS",
            "css-grid": "CSS",
            "css-system-font-stack": "CSS",
            "css-tricks": "CSS",
            "css": "CSS",
            "cssnext": "CSS",
            "sass": "CSS",
            "stylus": "CSS",

            # Databases
            "knex": "Databases",
            "mysql": "Databases",
            "postgresql-json": "Databases",
            "postgresql": "Databases",
            "sql-join": "Databases",

            # DevOps
            "awscli": "DevOps",
            "chef": "DevOps",
            "circle": "DevOps",
            "deis": "DevOps",
            "docker-compose": "DevOps",
            "docker": "DevOps",
            "dockerfile": "DevOps",
            "flynn": "DevOps",
            "heroku": "DevOps",
            "travis": "DevOps",
            "vagrant": "DevOps",
            "vagrantfile": "DevOps",

            # Elixir
            "elixir": "Elixir",
            "elixir-metaprogramming": "Elixir",
            "ets": "Elixir",
            "exunit": "Elixir",
            "phoenix": "Elixir",
            "phoenix-conn": "Elixir",
            "phoenix-ecto": "Elixir",
            "phoenix-ecto@1.2": "Elixir",
            "phoenix-migrations": "Elixir",
            "phoenix-routing": "Elixir",
            "phoenix@1.2": "Elixir",

            # Git
            "git": "Git",
            "git-branch": "Git",
            "git-extras": "Git",
            "git-log-format": "Git",
            "git-log": "Git",
            "git-revisions": "Git",
            "git-tricks": "Git",
            "tig": "Git",

            # HTML
            "appcache": "HTML",
            "applinks": "HTML",
            "html-email": "HTML",
            "html-input": "HTML",
            "html-meta": "HTML",
            "html-microformats": "HTML",
            "html-share": "HTML",
            "html": "HTML",
            "ie": "HTML",
            "ie_bugs": "HTML",
            "layout-thrashing": "HTML",
            "xpath": "HTML",

            # Java & JVM
            "kotlin": "Java & JVM",

            # JavaScript
            "canvas": "JavaScript",
            "dom-range": "JavaScript",
            "dom-selection": "JavaScript",
            "es6": "JavaScript",
            "js-appcache": "JavaScript",
            "js-array": "JavaScript",
            "js-date": "JavaScript",
            "js-fetch": "JavaScript",
            "js-lazy": "JavaScript",
            "js-speech": "JavaScript",
            "jsdoc": "JavaScript",
            "npm": "JavaScript",
            "promise": "JavaScript",
            "vue": "JavaScript",
            "vue@1.0.28": "JavaScript",
            "web-workers": "JavaScript",

            # JavaScript Libraries
            "101": "JavaScript Libraries",
            "angularjs": "JavaScript Libraries",
            "backbone": "JavaScript Libraries",
            "blessed": "JavaScript Libraries",
            "bluebird": "JavaScript Libraries",
            "bookshelf": "JavaScript Libraries",
            "browser-sync": "JavaScript Libraries",
            "browserify": "JavaScript Libraries",
            "camp": "JavaScript Libraries",
            "chai": "JavaScript Libraries",
            "co": "JavaScript Libraries",
            "commander.js": "JavaScript Libraries",
            "deku": "JavaScript Libraries",
            "deku@1": "JavaScript Libraries",
            "ember": "JavaScript Libraries",
            "expectjs": "JavaScript Libraries",
            "express": "JavaScript Libraries",
            "fastify": "JavaScript Libraries",
            "flow": "JavaScript Libraries",
            "gremlins": "JavaScript Libraries",
            "gulp": "JavaScript Libraries",
            "handlebars.js": "JavaScript Libraries",
            "harvey.js": "JavaScript Libraries",
            "immutable.js": "JavaScript Libraries",
            "jade": "JavaScript Libraries",
            "jasmine": "JavaScript Libraries",
            "jest": "JavaScript Libraries",
            "jquery": "JavaScript Libraries",
            "jquery-cdn": "JavaScript Libraries",
            "js-model": "JavaScript Libraries",
            "jscoverage": "JavaScript Libraries",
            "jshint": "JavaScript Libraries",
            "koa": "JavaScript Libraries",
            "lodash": "JavaScript Libraries",
            "meow": "JavaScript Libraries",
            "middleman": "JavaScript Libraries",
            "minimist": "JavaScript Libraries",
            "mobx": "JavaScript Libraries",
            "mocha": "JavaScript Libraries",
            "mocha-blanket": "JavaScript Libraries",
            "mocha-html": "JavaScript Libraries",
            "mocha-tdd": "JavaScript Libraries",
            "modella": "JavaScript Libraries",
            "modernizr": "JavaScript Libraries",
            "moment": "JavaScript Libraries",
            "nock": "JavaScript Libraries",
            "nopt": "JavaScript Libraries",
            "parsimmon": "JavaScript Libraries",
            "parsley": "JavaScript Libraries",
            "polyfill.io": "JavaScript Libraries",
            "pug": "JavaScript Libraries",
            "qjs": "JavaScript Libraries",
            "qunit": "JavaScript Libraries",
            "ractive": "JavaScript Libraries",
            "riot": "JavaScript Libraries",
            "rollup": "JavaScript Libraries",
            "sequelize": "JavaScript Libraries",
            "shelljs": "JavaScript Libraries",
            "sinon": "JavaScript Libraries",
            "sinon-chai": "JavaScript Libraries",
            "spine": "JavaScript Libraries",
            "stencil": "JavaScript Libraries",
            "superagent": "JavaScript Libraries",
            "tape": "JavaScript Libraries",
            "typescript": "JavaScript Libraries",
            "umdjs": "JavaScript Libraries",
            "underscore-string": "JavaScript Libraries",
            "virtual-dom": "JavaScript Libraries",
            "vows": "JavaScript Libraries",
            "webpack": "JavaScript Libraries",
            "weinre": "JavaScript Libraries",
            "yargs": "JavaScript Libraries",
            "yarn": "JavaScript Libraries",
            "zombie": "JavaScript Libraries",

            # Jekyll
            "gh-pages": "Jekyll",
            "jekyll-github": "Jekyll",
            "jekyll": "Jekyll",

            # Ledger
            "hledger": "Ledger",
            "ledger": "Ledger",
            "ledger-csv": "Ledger",
            "ledger-examples": "Ledger",
            "ledger-format": "Ledger",
            "ledger-periods": "Ledger",
            "ledger-query": "Ledger",

            # Markup
            "emmet": "Markup",
            "haml": "Markup",
            "kramdown": "Markup",
            "markdown": "Markup",
            "rdoc": "Markup",
            "rst": "Markup",
            "textile": "Markup",
            "tomdoc": "Markup",
            "yaml": "Markup",

            # macOS
            "applescript": "macOS",
            "macos-mouse-acceleration": "macOS",
            "osx": "macOS",

            # Node.js
            "nodejs": "Node.js",
            "nodejs-assert": "Node.js",
            "nodejs-fs": "Node.js",
            "nodejs-path": "Node.js",
            "nodejs-process": "Node.js",
            "nodejs-stream": "Node.js",
            "package-json": "Node.js",

            # PHP
            "php": "PHP",

            # Python
            "jinja": "Python",
            "mako": "Python",
            "python": "Python",

            # Rails
            "arel": "Rails",
            "rails": "Rails",
            "rails-controllers": "Rails",
            "rails-forms": "Rails",
            "rails-helpers": "Rails",
            "rails-i18n": "Rails",
            "rails-migrations": "Rails",
            "rails-models": "Rails",
            "rails-plugins": "Rails",
            "rails-routes": "Rails",
            "rails-tricks": "Rails",

            # React
            "awesome-redux": "React",
            "enzyme": "React",
            "enzyme@2": "React",
            "flux": "React",
            "react": "React",
            "react-router": "React",
            "react@0.14": "React",
            "redux": "React",

            # Ruby
            "activeadmin": "Ruby",
            "bundler": "Ruby",
            "goby": "Ruby",
            "minitest": "Ruby",
            "rake": "Ruby",
            "rbenv": "Ruby",
            "rspec": "Ruby",
            "rspec-rails": "Ruby",
            "ruby": "Ruby",
            "ruby21": "Ruby",
            "rubygems": "Ruby",
            "stimulus-reflex": "Ruby",

            # Ruby Libraries
            "capybara": "Ruby Libraries",
            "chunky_png": "Ruby Libraries",
            "do": "Ruby Libraries",
            "factory_bot": "Ruby Libraries",
            "ffaker": "Ruby Libraries",
            "machinist": "Ruby Libraries",
            "meta-tags": "Ruby Libraries",
            "packs": "Ruby Libraries",
            "pry": "Ruby Libraries",
            "psdrb": "Ruby Libraries",
            "rack-test": "Ruby Libraries",
            "ronn": "Ruby Libraries",
            "sequel": "Ruby Libraries",
            "slim": "Ruby Libraries",

            # Vim
            "projectionist": "Vim",
            "tabular": "Vim",
            "vim": "Vim",
            "vim-diff": "Vim",
            "vim-digraphs": "Vim",
            "vim-easyalign": "Vim",
            "vim-help": "Vim",
            "vim-rails": "Vim",
            "vim-unite": "Vim",
            "vimscript": "Vim",
            "vimscript-functions": "Vim",
            "vimscript-snippets": "Vim",

            # Others
            "bolt": "Others",
            "cask-index": "Others",
            "cheatsheet-styles": "Others",
            "cidr": "Others",
            "command_line": "Others",
            "cordova": "Others",
            "datetime": "Others",
            "devise": "Others",
            "divshot": "Others",
            "figlet": "Others",
            "firebase": "Others",
            "firefox": "Others",
            "freenode": "Others",
            "frequency-separation-retouching": "Others",
            "google-webfonts": "Others",
            "graphql": "Others",
            "http-status": "Others",
            "imagemagick": "Others",
            "ios-provision": "Others",
            "jinja2": "Others",
            "less": "Others",
            "licenses": "Others",
            "linux": "Others",
            "lua": "Others",
            "make-assets": "Others",
            "nocode": "Others",
            "pacman": "Others",
            "passenger": "Others",
            "perl-pie": "Others",
            "ph-food-delivery": "Others",
            "plantuml": "Others",
            "premailer": "Others",
            "regexp": "Others",
            "resolutions": "Others",
            "rest-api": "Others",
            "saucelabs": "Others",
            "semver": "Others",
            "siege": "Others",
            "simple_form": "Others",
            "social-images": "Others",
            "spreadsheet": "Others",
            "strftime": "Others",
            "ubuntu": "Others",
            "unicode": "Others",
            "vainglory": "Others",
            "watchman": "Others",
            "znc": "Others"
        } 

    async def get_sheets(self) -> List[Dict[str, str]]:
        """Get list of available cheat sheets."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cache: {e}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    sheets = []
                    
                    # Find all cheat sheet links
                    for link in soup.select('a[href^="/"]'):
                        href = link.get('href')
                        if href and href.startswith('/') and not href == '/':
                            title = link.get_text().strip()
                            if title:
                                sheets.append({
                                    'title': title,
                                    'path': href.lstrip('/')
                                })
                    
                    # Cache the sheets list
                    with open(self.cache_file, 'w') as f:
                        json.dump(sheets, f)
                    
                    return sheets
        except Exception as e:
            logger.error(f"Error fetching sheets: {e}")
            return []

    def is_synced(self) -> bool:
        """Check if the source is already synced."""
        try:
            # Check if cache directory exists
            if not self.cache_dir.exists():
                return False
                
            # Check if sheets list cache exists
            if not self.cache_file.exists():
                return False
                
            # Check if common sheets are cached
            for sheet in self.common_sheets:
                cache_path = self.sheets_cache / sheet
                if not cache_path.exists():
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            return False

    def sync(self) -> bool:
        """Synchronize cheat sheets locally."""
        try:
            # Create cache directory if it doesn't exist
            self.sheets_cache.mkdir(parents=True, exist_ok=True)
            
            # Get list of all files from GitHub API
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/vnd.github.v3+json"
            }
            
            logger.debug("Fetching repository tree from GitHub API...")
            response = httpx.get(self.api_url, headers=headers, timeout=10.0)
            
            if response.status_code != 200:
                logger.error(f"GitHub API returned status code {response.status_code}")
                return False
                
            data = response.json()
            md_files = [item['path'] for item in data.get('tree', []) 
                       if item.get('path', '').endswith('.md')]
            
            # First sync common sheets
            for sheet in self.common_sheets:
                if sheet in md_files:
                    try:
                        url = f"{self.base_url}/{sheet}"
                        sheet_response = httpx.get(url, headers=headers)
                        if sheet_response.status_code == 200:
                            sheet_path = self.sheets_cache / sheet
                            sheet_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(sheet_path, 'w', encoding='utf-8') as f:
                                f.write(sheet_response.text)
                            logger.debug(f"Cached {sheet}")
                    except Exception as e:
                        logger.error(f"Error syncing {sheet}: {e}")
                        continue
            
            # Cache the file list
            with open(self.cache_file, 'w') as f:
                json.dump(md_files, f)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return False

    async def get_sheet(self, path: str) -> Optional[str]:
        """Get a specific cheat sheet by path."""
        cache_path = self.sheets_cache / f"{path}.html"
        
        # Check cache first
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        
        # Fetch from website if not in cache
        try:
            url = f"{self.base_url}/{path}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    content = response.text
                    # Cache the result
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return content
                else:
                    return None
        except Exception as e:
            logger.error(f"Error fetching sheet: {e}")
            return None 